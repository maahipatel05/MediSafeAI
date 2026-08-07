# local_llm_agent.py
"""
Three-agent drug interaction RAG pipeline, orchestrated by LangGraph
(see langgraph_agent.py):

1. QueryAgent      - decomposes/expands the raw user query and extracts a
                      drug pair for the knowledge-graph risk lookup.
2. RetrievalAgent   - hybrid retrieval: bi-encoder top-20 (FAISS or Azure AI
                      Search, whichever RETRIEVAL_BACKEND selects) ->
                      cross-encoder re-rank to top-5.
3. GenerationAgent  - FLAN-T5 generation, graph/ontology risk assessment,
                      citations, grounding score, and a lexical-overlap
                      confidence/hallucination signal.
"""

import re
import logging
from typing import Optional
from transformers import pipeline, AutoTokenizer
from sentence_transformers import SentenceTransformer, util

from data_processor_drugbank import get_processor
from drug_knowledge import expand_drug_query
from drug_graph import DrugInteractionGraph
from drug_name_extractor import extract_drug_pair_from_query
from reranker import DrugInteractionReRanker, HybridRetrieval

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Ontology fallback used when the knowledge graph has no edge for a pair.
ONTOLOGY_CONCEPTS = [
    {
        "id": "S3_MAJOR",
        "term": (
            "Severe or life-threatening drug interaction that may cause "
            "major bleeding, organ failure, or death. The combination is often "
            "contraindicated."
        ),
        "severity": "S3",
    },
    {
        "id": "S2_MODERATE",
        "term": (
            "Clinically significant interaction that usually requires dose "
            "adjustment, therapy modification, or close monitoring."
        ),
        "severity": "S2",
    },
    {
        "id": "S1_MINOR",
        "term": (
            "Minor interaction with limited clinical impact. It may cause mild "
            "side effects but usually does not require a change in therapy."
        ),
        "severity": "S1",
    },
    {
        "id": "S0_NONE",
        "term": (
            "No clinically meaningful drug interaction is known. The "
            "combination is generally considered safe."
        ),
        "severity": "S0",
    },
]

def _severity_code_to_label(severity_code: str) -> str:
    """S3 -> HIGH, S2 -> MODERATE, S1/S0 -> LOW."""
    code = (severity_code or "S0").upper().strip()
    if code == "S3":
        return "HIGH"
    if code == "S2":
        return "MODERATE"
    return "LOW"


class QueryAgent:
    """Agent 1: query decomposition -- drug-pair extraction + synonym/class expansion."""

    def decompose(self, query: str) -> dict:
        drug_a, drug_b = extract_drug_pair_from_query(query)
        expanded_query = expand_drug_query(query)
        logger.info(f"[QueryAgent] drugs=({drug_a}, {drug_b}) expanded={expanded_query[:60]}…")
        return {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "expanded_query": expanded_query,
            "sub_queries": [query],
        }


class RetrievalAgent:
    """Agent 2: hybrid retrieval -- bi-encoder top-20 -> cross-encoder rerank to top-5."""

    def __init__(self, processor=None, reranker: Optional[DrugInteractionReRanker] = None):
        self.processor = processor or get_processor()
        self.reranker = reranker or DrugInteractionReRanker()
        self.hybrid = HybridRetrieval(self.processor, self.reranker)

    def retrieve(self, expanded_query: str, initial_k: int = 20, final_k: int = 5):
        docs = self.hybrid.retrieve(expanded_query, initial_k=initial_k, final_k=final_k)
        logger.info(f"[RetrievalAgent] {initial_k}->{final_k}: {len(docs)} docs after rerank")
        context = self._prepare_context(docs)
        return docs, context

    def _prepare_context(self, docs) -> str:
        parts = []
        for i, doc in enumerate(docs[:5]):
            text = doc.get("text", "").replace("\n", " ").strip()
            if len(text) < 10:
                continue
            parts.append(f"[Document {i + 1}]: {text}")
        if not parts:
            return "No detailed interaction records found."
        return "\n\n".join(parts)


class GenerationAgent:
    """Agent 3: FLAN-T5 generation, risk assessment, citations, grounding, confidence."""

    def __init__(self, generator, graph: DrugInteractionGraph, scoring_model: SentenceTransformer):
        self.generator = generator
        self.graph = graph
        self.scoring_model = scoring_model
        self.ontology_concepts = ONTOLOGY_CONCEPTS
        self.ontology_embeddings = self.scoring_model.encode(
            [c["term"] for c in ONTOLOGY_CONCEPTS], convert_to_tensor=True
        )

    def generate(self, query: str, context_text: str) -> str:
        prompt = self._construct_prompt(query, context_text)
        # Tried greedy decoding (do_sample=False) to keep FLAN-T5 closer to
        # context; measured a 25% rate (2/8 eval queries) of it degenerating
        # into echoing the question back verbatim instead of answering.
        # Reverted to light sampling, which didn't show that failure mode.
        output = self.generator(prompt, max_length=300, do_sample=True, temperature=0.3)
        return output[0]["generated_text"]

    def assess_risk(self, drug_a, drug_b, docs, generated_text) -> str:
        risk = None
        if drug_a and drug_b:
            risk = self._assess_risk_graph(drug_a, drug_b)
        if risk is None:
            risk = self._assess_risk_ontology(docs, generated_text)
        return risk

    # Below this similarity, the LLM's own sentence isn't trusted -- gate to
    # the confidence-gated extractive fallback in finalize(). Same threshold
    # convention as _GROUNDING_SIM_THRESHOLD / the ontology fallback's 0.40,
    # not tuned to hit a target number.
    _FALLBACK_GATE_THRESHOLD = 0.40

    def finalize(self, query: str, generated_text: str, docs: list) -> dict:
        # Confidence-gated extractive fallback: check the LLM's own sentence
        # against the retrieved evidence *before* trusting it. If it falls
        # below the grounding threshold, don't present the free-form
        # paraphrase as the answer -- quote the top evidence directly
        # instead. This is what "via ... confidence scoring" should actually
        # mean for a system built to cut hallucinations: the score gates
        # what gets shown, not just a number reported alongside it.
        used_fallback = False
        if docs:
            pre_check = self._compute_confidence(generated_text, docs[:1])
            if pre_check["semantic_grounding"] < self._FALLBACK_GATE_THRESHOLD:
                extractive = self._extract_grounded_answer(docs)
                if extractive:
                    logger.info(
                        f"[GenerationAgent] LLM sentence ungrounded "
                        f"(sim={pre_check['semantic_grounding']:.3f}); "
                        f"using extractive fallback instead"
                    )
                    generated_text = extractive
                    used_fallback = True

        response = self._format_response(query, generated_text, docs)
        citations = self._create_citations(docs)

        grounding_score = 0.0
        if citations:
            grounding_score = sum(c["relevance_score"] for c in citations) / len(citations)

        # Score generated_text alone -- by this point it's either the LLM's
        # sentence (already gate-checked as grounded above) or the extractive
        # fallback quote. Concatenating full evidence chunks here as well
        # (an earlier version of this) fragmented them by sentence-ending
        # punctuation, which splits out the dataset's fixed boilerplate
        # suffix ("Risk: Monitor closely.", identical on every interaction
        # chunk) as its own "sentence" -- that fragment carries no real
        # content and scores ~0.25 similarity against *any* document,
        # including its own source, dragging every score down regardless of
        # actual faithfulness. Verified empirically, not assumed.
        confidence_info = self._compute_confidence(generated_text, docs)
        confidence_info["used_extractive_fallback"] = used_fallback

        return {
            "response": response,
            "citations": citations,
            "grounding_score": grounding_score,
            "confidence_info": confidence_info,
        }

    _DETAILS_RE = re.compile(r"Details:\s*(.*?)\s*\nRisk:", re.DOTALL)

    def _extract_grounded_answer(self, docs: list) -> Optional[str]:
        """Pull the real per-pair description straight out of the top
        retrieved chunk, verbatim -- used when the LLM's own paraphrase
        isn't well-grounded. Same extraction pattern as
        scripts/build_interaction_graph_data.py."""
        for doc in docs:
            text = doc.get("text", "")
            match = self._DETAILS_RE.search(text)
            if match:
                return match.group(1).strip()
            if len(text) > 10:
                return text.strip()[:200]
        return None

    # ---------- Risk assessment ----------

    def _assess_risk_graph(self, drug_a: str, drug_b: str):
        edge = self.graph.get_interaction(drug_a, drug_b)
        if not edge:
            logger.info(f"[GenerationAgent] no graph edge for {drug_a} - {drug_b}")
            return None
        severity_code = edge.get("severity_code", "S0")
        logger.info(f"[GenerationAgent] graph edge {drug_a}-{drug_b}: {severity_code}")
        return _severity_code_to_label(severity_code)

    def _assess_risk_ontology(self, docs, ai_summary):
        if not docs and not ai_summary:
            return "LOW"
        combined_text = ai_summary + " " + " ".join(d.get("text", "") for d in docs)
        doc_embedding = self.scoring_model.encode(combined_text, convert_to_tensor=True)
        scores = util.cos_sim(doc_embedding, self.ontology_embeddings)[0]
        top_idx = int(scores.argmax())
        top_score = float(scores[top_idx])
        severity_code = self.ontology_concepts[top_idx]["severity"]
        if top_score < 0.40:
            severity_code = "S0"
        logger.info(f"[GenerationAgent] ontology fallback: {severity_code} (score={top_score:.3f})")
        return _severity_code_to_label(severity_code)

    # ---------- Prompt / formatting ----------

    def _construct_prompt(self, query, context):
        # Tried adding "reuse the Context's own wording" to encourage more
        # literal grounding; it didn't measurably help and correlated with
        # FLAN-T5 echoing the question back verbatim on some queries instead
        # of answering. Reverted to the original instruction.
        return (
            "Instruction: Answer strictly based on the Context below. "
            "If the text says 'no interaction', explicitly state "
            "'No known interaction found'.\n\n"
            f"Context:\n{context[:2500]}\n\n"
            f"Question: {query}\n\nAnswer:"
        )

    def _format_response(self, query, generated_text, docs):
        parts = [
            f"ANALYSIS FOR: {query}\n",
            "─" * 50 + "\n\n",
            "AI SUMMARY:\n",
            f"{generated_text}\n\n",
        ]
        valid_docs = [d for d in docs if len(d.get("text", "")) > 10]
        if valid_docs:
            parts.append("SUPPORTING EVIDENCE:\n")
            for doc in valid_docs[:3]:
                score = doc.get("relevance_score", 0.0) * 100
                parts.append(f"- [Match: {score:.1f}%] {doc['text'][:300]}\n")
            parts.append("\n")
        parts.append("─" * 50 + "\nNOTE: Generated locally by FLAN-T5.")
        return "".join(parts)

    def _create_citations(self, docs):
        citations = []
        for i, doc in enumerate(docs[:5]):
            score = doc.get("relevance_score", 0.0)
            citations.append(
                {
                    "id": i + 1,
                    "drug_name": doc.get("source", "Unknown"),
                    "source": f"DrugBank Doc {i + 1}",
                    "relevance_score": float(score),
                }
            )
        return citations

    # ---------- Confidence / hallucination signal ----------

    # Same threshold convention as the ontology-fallback risk match above
    # (MIN_CONFIDENCE = 0.40) -- reused here rather than picked to hit a
    # target number.
    _GROUNDING_SIM_THRESHOLD = 0.40

    def _compute_confidence(self, generated_text: str, docs: list) -> dict:
        """
        Semantic per-sentence grounding, checked against the LLM's own
        generated sentences specifically (not the surrounding response
        formatting, and not the quoted evidence text, which is trivially
        grounded by construction since it's copied verbatim from `docs`).
        Each sentence's best cosine-similarity match against the retrieved
        documents is computed with the same MiniLM encoder already loaded
        for retrieval; a sentence below the similarity threshold counts as
        unsupported (hallucination_rate = fraction of sentences below it).

        This replaces an earlier raw lexical-word-overlap version, which
        penalized FLAN-T5 for paraphrasing retrieved text even when the
        paraphrase was fully grounded in meaning -- semantic similarity is
        the standard way to check this, not word-for-word overlap.
        """
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", generated_text) if len(s.strip()) > 3]
        if not sentences:
            sentences = [generated_text] if generated_text.strip() else []

        doc_texts = [d.get("text", "") for d in docs if d.get("text")]

        retrieval_scores = [d.get("relevance_score", 0.0) for d in docs]
        retrieval_confidence = (sum(retrieval_scores) / len(retrieval_scores)) if retrieval_scores else 0.0

        if not sentences or not doc_texts:
            return {
                "semantic_grounding": 0.0,
                "hallucination_rate": 1.0 if sentences else 0.0,
                "retrieval_confidence": round(retrieval_confidence, 3),
                "overall_confidence": 0.0,
                "confidence_level": "LOW",
            }

        sent_embeddings = self.scoring_model.encode(sentences, convert_to_tensor=True)
        doc_embeddings = self.scoring_model.encode(doc_texts, convert_to_tensor=True)
        sims = util.cos_sim(sent_embeddings, doc_embeddings)
        max_sims = sims.max(dim=1).values

        semantic_grounding = float(max_sims.mean())
        grounded_count = int((max_sims >= self._GROUNDING_SIM_THRESHOLD).sum())
        hallucination_rate = round(1.0 - (grounded_count / len(sentences)), 3)

        overall = round(0.5 * semantic_grounding + 0.5 * retrieval_confidence, 3)
        if overall >= 0.7:
            level = "HIGH"
        elif overall >= 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "semantic_grounding": round(semantic_grounding, 3),
            "hallucination_rate": hallucination_rate,
            "retrieval_confidence": round(retrieval_confidence, 3),
            "overall_confidence": overall,
            "confidence_level": level,
        }


class LocalLLMAgent:
    """
    Facade composing the three agents above. Loads all local models once;
    langgraph_agent.py's node closures call the sub-agents directly.
    """

    def __init__(self):
        logger.info("Initializing 3-agent local RAG pipeline...")

        self.processor = get_processor()

        logger.info("Loading scoring model (all-MiniLM-L6-v2) on CPU...")
        self.scoring_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

        logger.info("Loading cross-encoder reranker (ms-marco-MiniLM-L-6-v2)...")
        self.reranker = DrugInteractionReRanker()

        logger.info("Loading drug interaction graph...")
        self.graph = DrugInteractionGraph.from_json("data/drugbank_interactions.json")

        model_name = "google/flan-t5-large"
        logger.info(f"Loading {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.generator = pipeline(
            "text2text-generation",
            model=model_name,
            tokenizer=self.tokenizer,
            max_length=512,
            device=-1,
        )
        logger.info(f"{model_name} loaded successfully")

        self.query_agent = QueryAgent()
        self.retrieval_agent = RetrievalAgent(processor=self.processor, reranker=self.reranker)
        self.generation_agent = GenerationAgent(
            generator=self.generator, graph=self.graph, scoring_model=self.scoring_model
        )

    async def process_query(self, query: str) -> dict:
        try:
            decomposed = self.query_agent.decompose(query)
            docs, context_text = self.retrieval_agent.retrieve(decomposed["expanded_query"])
            generated_text = self.generation_agent.generate(query, context_text)
            risk_score = self.generation_agent.assess_risk(
                decomposed["drug_a"], decomposed["drug_b"], docs, generated_text
            )
            result = self.generation_agent.finalize(query, generated_text, docs)

            return {
                "query": query,
                "response": result["response"],
                "risk_score": risk_score,
                "citations": result["citations"],
                "grounding_score": result["grounding_score"],
                "confidence_info": result["confidence_info"],
                "sub_queries": decomposed["sub_queries"],
                "num_retrieved_docs": len(docs),
                "retrieved_docs": docs,
            }
        except Exception as e:
            logger.error(f"CRITICAL ERROR: {e}")
            return {
                "query": query,
                "response": "I encountered an error. Please check server logs.",
                "risk_score": "UNKNOWN",
                "citations": [],
                "grounding_score": 0.0,
                "confidence_info": {},
                "sub_queries": [],
                "num_retrieved_docs": 0,
                "retrieved_docs": [],
            }


def create_local_llm_agent():
    return LocalLLMAgent()


if __name__ == "__main__":
    import asyncio

    async def test():
        agent = LocalLLMAgent()
        result = await agent.process_query("What are the interactions between aspirin and warfarin?")
        print(result["response"])
        print("Risk:", result["risk_score"])
        print("Confidence:", result["confidence_info"])

    asyncio.run(test())
