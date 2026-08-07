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

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "been", "have", "has", "had", "not", "but", "can", "may", "will", "would",
    "could", "should", "when", "what", "which", "who", "its", "their", "them",
    "they", "you", "your", "about", "into", "than", "then", "there", "these",
    "those", "also", "such", "does", "did", "doing", "over", "under",
}


def _content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-zA-Z]{3,}", text.lower())} - _STOPWORDS


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
        output = self.generator(prompt, max_length=300, do_sample=True, temperature=0.3)
        return output[0]["generated_text"]

    def assess_risk(self, drug_a, drug_b, docs, generated_text) -> str:
        risk = None
        if drug_a and drug_b:
            risk = self._assess_risk_graph(drug_a, drug_b)
        if risk is None:
            risk = self._assess_risk_ontology(docs, generated_text)
        return risk

    def finalize(self, query: str, generated_text: str, context_text: str, docs: list) -> dict:
        response = self._format_response(query, generated_text, docs)
        citations = self._create_citations(docs)

        grounding_score = 0.0
        if citations:
            grounding_score = sum(c["relevance_score"] for c in citations) / len(citations)

        confidence_info = self._compute_confidence(generated_text, context_text, docs)

        return {
            "response": response,
            "citations": citations,
            "grounding_score": grounding_score,
            "confidence_info": confidence_info,
        }

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
            top_doc = valid_docs[0]
            score = top_doc.get("relevance_score", 0.0) * 100
            parts.append("TOP EVIDENCE:\n")
            parts.append(f"- [Match: {score:.1f}%] {top_doc['text'][:150]}...\n\n")
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

    def _compute_confidence(self, generated_text: str, context_text: str, docs: list) -> dict:
        """
        Lightweight, real (not fabricated) grounding check: what fraction of
        the generation's content words are attested in the retrieved
        context? Low overlap is treated as a hallucination signal. Combined
        with the reranker's own retrieval confidence into one score.
        """
        gen_words = _content_words(generated_text)
        ctx_words = _content_words(context_text)

        lexical_overlap = (len(gen_words & ctx_words) / len(gen_words)) if gen_words else 0.0
        hallucination_rate = round(1.0 - lexical_overlap, 3)

        retrieval_scores = [d.get("relevance_score", 0.0) for d in docs]
        retrieval_confidence = (sum(retrieval_scores) / len(retrieval_scores)) if retrieval_scores else 0.0

        overall = round(0.5 * lexical_overlap + 0.5 * retrieval_confidence, 3)
        if overall >= 0.7:
            level = "HIGH"
        elif overall >= 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "lexical_grounding_overlap": round(lexical_overlap, 3),
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
            result = self.generation_agent.finalize(query, generated_text, context_text, docs)

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
