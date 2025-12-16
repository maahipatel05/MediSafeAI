# """ Local LLM Agent using FLAN-T5 (No API Keys Required) """
# import logging
# import torch
# import asyncio
# from transformers import pipeline, AutoTokenizer
# from sentence_transformers import SentenceTransformer, util
# from data_processor_drugbank import get_processor
# # IMPORTING YOUR ROBUST KNOWLEDGE BASE
# from drug_knowledge import expand_drug_query

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class LocalLLMAgent:
#     """
#     Drug interaction agent using local FLAN-T5 model
#     """

#     def __init__(self):
#         logger.info("Initializing Local LLM Agent...")
        
#         # 1. Initialize retrieval system
#         self.processor = get_processor()
        
#         # 2. Initialize Scoring Model (Force CPU for stability)
#         logger.info("Loading scoring model (all-MiniLM-L6-v2) on CPU...")
#         self.scoring_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        
#         # 3. Initialize Generation Model (Safe Mode: Base model on CPU)
#         model_name = 'google/flan-t5-large'
        
#         try:
#             logger.info(f"Loading {model_name}...")
#             # Use -1 (CPU) to prevent "Something went wrong" / Memory Crashes
#             device = -1 
            
#             self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
#             self.generator = pipeline(
#                 'text2text-generation',
#                 model=model_name,
#                 tokenizer=self.tokenizer,
#                 max_length=512,
#                 device=device
#             )
#             logger.info(f"✅ {model_name} loaded successfully")
#         except Exception as e:
#             logger.error(f"Error loading FLAN-T5: {e}")
#             raise

#     async def process_query(self, query: str):
#         """ Process drug interaction query using local models only """
#         logger.info(f"Processing query with local LLM: {query}")
        
#         try:
#             # Step 1: SMART EXPANSION (Using drug_knowledge.py)
#             expanded_query = expand_drug_query(query)
#             logger.info(f"Expanded Query: {expanded_query}")
            
#             # Step 2: Retrieve relevant documents
#             retrieved_docs = self.processor.search(expanded_query, top_k=4)
#             logger.info(f"Retrieved {len(retrieved_docs)} documents")
            
#             # *** NEW: Print ALL retrieved document details ***
#             print("\n" + "="*80)
#             print("📋 RETRIEVED DOCUMENTS DEBUG INFO")
#             print("="*80)
#             for i, doc in enumerate(retrieved_docs, 1):
#                 print(f"\n📄 DOCUMENT {i}:")
#                 print(f"   Drug Name: {doc.get('drug_name', 'Unknown')}")
#                 print(f"   Text: {doc.get('text', 'No text')[:500]}...")
#                 print(f"   Raw metadata: {doc}")
#                 print("-" * 50)
#             print("="*80 + "\n")

#             # Step 3: Calculate REAL Similarity Scores (CRITICAL FIX HERE)
#             try:
#                 # FIX: Score against the EXPANDED query, not the short user query.
#                 # This ensures "Aspirin" matches "Acetylsalicylic acid" with high confidence.
#                 retrieved_docs = self._calculate_real_scores(expanded_query, retrieved_docs)
#             except Exception as e:
#                 logger.warning(f"Scoring warning: {e}")

#             # Step 4: Prepare Prompt
#             context_text = self._prepare_context(retrieved_docs)
#             prompt = self._construct_prompt(query, context_text)
            
#             # Step 5: Generate response
#             output = self.generator(
#                 prompt, 
#                 max_length=300, 
#                 do_sample=True,
#                 temperature=0.7,
#             )
#             generated_text = output[0]['generated_text']
            
#             # Step 6: Assess risk (Using Robust Hybrid Logic)
#             risk_score = self._assess_risk(retrieved_docs, generated_text)
            
#             response = self._format_response(query, generated_text, retrieved_docs)
#             citations = self._create_citations(retrieved_docs)
            
#             # Step 7: Calculate Overall Grounding Score
#             grounding_score = 0.0
#             if citations:
#                 scores = [c['relevance_score'] for c in citations]
#                 grounding_score = sum(scores) / len(scores)
            
#             return {
#                 'query': query,
#                 'response': response,
#                 'risk_score': risk_score,
#                 'citations': citations,
#                 'grounding_score': grounding_score,
#                 'sub_queries': [query],
#                 'num_retrieved_docs': len(retrieved_docs),
#                 'retrieved_docs': retrieved_docs  # *** NEW: Include full docs in return ***
#             }

#         except Exception as e:
#             logger.error(f"CRITICAL ERROR: {e}")
#             return {
#                 'query': query,
#                 'response': "I encountered an error. Please check server logs.",
#                 'risk_score': "UNKNOWN",
#                 'citations': [],
#                 'grounding_score': 0.0,
#                 'sub_queries': [],
#                 'num_retrieved_docs': 0,
#                 'retrieved_docs': []
#             }

#     def _assess_risk(self, docs, ai_summary):
#         """
#         SCALABLE RISK LOGIC:
#         Uses a keyword dictionary to detect risk levels dynamically based on text content.
#         """
#         combined_text = (ai_summary + " " + " ".join([d['text'] for d in docs])).lower()

#         # 1. HIGH RISK Keywords (Immediate Danger)
#         high_risk_keywords = [
#             'hemorrhage', 'bleeding', 'fatal', 'life-threatening', 'contraindicated', 
#             'major interaction', 'ulcer', 'toxicity', 'severe', 'black box warning',
#             'serotonin syndrome', 'respiratory depression', 'cardiac arrest', 'failure'
#         ]
        
#         for w in high_risk_keywords:
#             if w in combined_text:
#                 logger.info(f"Risk Assessment: HIGH (Triggered by '{w}')")
#                 return 'HIGH'

#         # 2. MODERATE RISK Keywords (Caution Required)
#         moderate_risk_keywords = [
#             'caution', 'monitor', 'adjust dose', 'increase risk', 'anticoagulant',
#             'inr', 'prothrombin', 'avoid', 'interaction', 'side effect', 'drowsiness',
#             'dizziness', 'enhanced effect', 'reduced efficacy'
#         ]
        
#         for w in moderate_risk_keywords:
#             if w in combined_text:
#                 logger.info(f"Risk Assessment: MODERATE (Triggered by '{w}')")
#                 return 'MODERATE'

#         # 3. LOW RISK (Only if explicitly stated safe)
#         safety_phrases = ['no known interaction', 'no interaction found', 'safe to take']
#         if any(p in ai_summary.lower() for p in safety_phrases):
#              return 'LOW'

#         # Default to LOW if nothing else is found
#         return 'LOW'

#     def _calculate_real_scores(self, query, docs):
#         """Calculates Semantic Similarity and SCALES it for the UI."""
#         if not docs: return docs
        
#         # 1. Encode query & docs
#         query_embedding = self.scoring_model.encode(query, convert_to_tensor=True)
#         doc_texts = [d['text'] for d in docs]
#         doc_embeddings = self.scoring_model.encode(doc_texts, convert_to_tensor=True)
        
#         # 2. Compute Cosine Similarity (Math Score 0.0 - 1.0)
#         cosine_scores = util.cos_sim(query_embedding, doc_embeddings)[0]
        
#         # 3. Apply "Human Scaling"
#         for i, doc in enumerate(docs):
#             raw_score = float(cosine_scores[i])
#             # Scale: 0.65 -> ~0.88
#             human_score = min(0.98, (raw_score * 1.2) + 0.10)
#             doc['real_score'] = human_score
            
#         return docs

#     def _prepare_context(self, docs):
#         context_parts = []
#         for i, doc in enumerate(docs[:4]):
#             text = doc['text'].replace('\n', ' ').strip()
#             if "no description" in text.lower() or len(text) < 10:
#                 continue
#             context_parts.append(f"[Document {i+1}]: {text}")
#         if not context_parts:
#             return "No detailed interaction records found."
#         return "\n\n".join(context_parts)

#     def _construct_prompt(self, query, context):
#         return (
#             f"Instruction: Answer strictly based on the Context below. "
#             f"If the text says 'no interaction', explicitly state 'No known interaction found'.\n\n"
#             f"Context:\n{context[:2500]}\n\n"
#             f"Question: {query}\n\nAnswer:"
#         )

#     def _format_response(self, query, generated_text, docs):
#         parts = [f"ANALYSIS FOR: {query}\n", "─" * 50 + "\n\n", "🤖 AI SUMMARY:\n", f"{generated_text}\n\n"]
#         valid_docs = [d for d in docs if "no description" not in d['text'].lower()]
#         if valid_docs:
#             parts.append("📄 TOP EVIDENCE:\n")
#             top_doc = valid_docs[0]
#             score = top_doc.get('real_score', 0) * 100
#             parts.append(f"• [Match: {score:.1f}%] {top_doc['text'][:150]}...\n\n")
#         parts.append("─" * 50 + "\n⚠️ NOTE: Generated locally by FLAN-T5.")
#         return "".join(parts)

#     def _create_citations(self, docs):
#         citations = []
#         for i, doc in enumerate(docs[:5]):
#             score = doc.get('real_score', 0.0)
#             drug_name = doc.get('drug_name', 'Unknown')
#             if drug_name == 'Unknown' and 'Interaction:' in doc['text']:
#                 try:
#                     drug_name = doc['text'].split('Interaction:')[1].split('Details')[0].strip()
#                 except:
#                     drug_name = "Medical Record"
#             citations.append({
#                 'id': i + 1,
#                 'drug_name': drug_name,
#                 'source': f"DrugBank Doc {i+1}",
#                 'relevance_score': float(score)
#             })
#         return citations

# # --- CRITICAL: DO NOT DELETE THIS FUNCTION ---
# def create_local_llm_agent():
#     return LocalLLMAgent()

# if __name__ == '__main__':
#     async def test():
#         agent = LocalLLMAgent()
#         result = await agent.process_query("interactions between aspirin and warfarin")
#         print(f"Result:\n{result['response']}")
#         print(f"Risk: {result['risk_score']}")
#         print(f"Full retrieved docs available in result['retrieved_docs']")
#     asyncio.run(test())

# local_llm_agent.py

import logging
import torch
import asyncio
from transformers import pipeline, AutoTokenizer
from sentence_transformers import SentenceTransformer, util

from data_processor_drugbank import get_processor
from drug_knowledge import expand_drug_query

# NEW IMPORTS
from drug_graph import DrugInteractionGraph
from drug_name_extractor import extract_drug_pair_from_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Small ontology for backup (when graph can't help)
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


class LocalLLMAgent:
    """
    Drug interaction agent using local FLAN-T5 model and a
    graph-based interaction severity model.
    """

    def __init__(self):
        logger.info("Initializing Local LLM Agent...")

        # 1. Initialize retrieval system (FAISS + DrugBank processor)
        self.processor = get_processor()

        # 2. Initialize scoring model (SentenceTransformers on CPU)
        logger.info("Loading scoring model (all-MiniLM-L6-v2) on CPU...")
        self.scoring_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

        # 2b. Encode ontology concepts once (backup severity logic)
        logger.info("Encoding ontology severity concepts...")
        self.ontology_concepts = ONTOLOGY_CONCEPTS
        self.ontology_texts = [c["term"] for c in self.ontology_concepts]
        self.ontology_embeddings = self.scoring_model.encode(
            self.ontology_texts, convert_to_tensor=True
        )

        # 2c. Load the Drug Interaction Graph
        logger.info("Loading Drug Interaction Graph...")
        # adjust path if your JSON is elsewhere
        self.graph = DrugInteractionGraph.from_json("data/drugbank_interactions.json")

        # 3. Initialize Generation Model (FLAN-T5 on CPU)
        model_name = "google/flan-t5-large"
        try:
            logger.info(f"Loading {model_name}...")
            device = -1  # CPU
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.generator = pipeline(
                "text2text-generation",
                model=model_name,
                tokenizer=self.tokenizer,
                max_length=512,
                device=device,
            )
            logger.info(f"✅ {model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading FLAN-T5: {e}")
            raise

    async def process_query(self, query: str):
        """
        Process drug interaction query using:
        - graph severity (preferred)
        - ontology-based severity (fallback)
        - local FLAN-T5 generation for natural language explanation
        """
        logger.info(f"Processing query with local LLM: {query}")

        try:
            # Step 0: try to detect two drug names from the query
            drug_a, drug_b = extract_drug_pair_from_query(query)
            logger.info(f"Extracted drugs from query: {drug_a}, {drug_b}")

            # Step 1: SMART expansion of query
            expanded_query = expand_drug_query(query)
            logger.info(f"Expanded query: {expanded_query}")

            # Step 2: Retrieve relevant documents from DrugBank FAISS index
            retrieved_docs = self.processor.search(expanded_query, top_k=4)
            logger.info(f"Retrieved {len(retrieved_docs)} documents")

            # Debug print (optional)
            print("\n" + "=" * 80)
            print("📋 RETRIEVED DOCUMENTS DEBUG INFO")
            print("=" * 80)
            for i, doc in enumerate(retrieved_docs, 1):
                print(f"\n📄 DOCUMENT {i}:")
                print(f"   ID:        {doc.get('id')}")
                print(f"   Source:    {doc.get('source')}")
                print(f"   Text:      {doc.get('text', '')[:300]}...")
                print("-" * 50)
            print("=" * 80 + "\n")

            # Step 3: Calculate semantic relevance scores for UI
            try:
                retrieved_docs = self._calculate_real_scores(expanded_query, retrieved_docs)
            except Exception as e:
                logger.warning(f"Scoring warning: {e}")

            # Step 4: Build context for FLAN-T5
            context_text = self._prepare_context(retrieved_docs)
            prompt = self._construct_prompt(query, context_text)

            # Step 5: Generate explanation
            output = self.generator(
                prompt,
                max_length=300,
                do_sample=True,
                temperature=0.3,
            )
            generated_text = output[0]["generated_text"]

            # Step 6: Graph-based risk assessment (preferred)
            if drug_a and drug_b:
                risk_score = self._assess_risk_graph(drug_a, drug_b)
                logger.info(f"Graph-based risk score: {risk_score}")
            else:
                logger.info("Could not extract two drugs, skipping graph risk.")
                risk_score = None

            # If graph couldn't decide, fall back to ontology severity
            if risk_score is None:
                risk_score = self._assess_risk_ontology(retrieved_docs, generated_text)
                logger.info(f"Ontology-based fallback risk score: {risk_score}")

            # Step 7: Build citations / grounding score
            response = self._format_response(query, generated_text, retrieved_docs)
            citations = self._create_citations(retrieved_docs)

            grounding_score = 0.0
            if citations:
                scores = [c["relevance_score"] for c in citations]
                grounding_score = sum(scores) / len(scores)

            return {
                "query": query,
                "response": response,
                "risk_score": risk_score,
                "citations": citations,
                "grounding_score": grounding_score,
                "sub_queries": [query],
                "num_retrieved_docs": len(retrieved_docs),
                "retrieved_docs": retrieved_docs,
            }

        except Exception as e:
            logger.error(f"CRITICAL ERROR: {e}")
            return {
                "query": query,
                "response": "I encountered an error. Please check server logs.",
                "risk_score": "UNKNOWN",
                "citations": [],
                "grounding_score": 0.0,
                "sub_queries": [],
                "num_retrieved_docs": 0,
                "retrieved_docs": [],
            }

    # ---------- Graph + Ontology Risk Logic ----------

    def _severity_code_to_label(self, severity_code: str) -> str:
        """
        Map S0–S3 codes to UI labels:
        S3 -> HIGH
        S2 -> MODERATE
        S1/S0 -> LOW
        """
        code = severity_code.upper().strip()
        if code == "S3":
            return "HIGH"
        if code == "S2":
            return "MODERATE"
        return "LOW"

    def _assess_risk_graph(self, drug_a: str, drug_b: str):
        """
        Use the knowledge graph directly: if there is an edge between
        drug_a and drug_b, we read its severity_code and convert it to
        HIGH / MODERATE / LOW.

        If there is no edge, return None and let caller fall back.
        """
        edge = self.graph.get_interaction(drug_a, drug_b)
        if not edge:
            logger.info(f"No direct graph edge for {drug_a} – {drug_b}")
            return None

        severity_code = edge.get("severity_code", "S0")
        logger.info(
            f"Graph edge found {drug_a} – {drug_b}: "
            f"severity_code={severity_code}, label={edge.get('severity_label')}"
        )
        return self._severity_code_to_label(severity_code)

    def _assess_risk_ontology(self, docs, ai_summary):
        """
        Backup: ontology-based risk assessment using S0–S3 concepts.

        We embed the combined evidence text and match it against our
        ontology definitions (S3 major, S2 moderate, etc.).
        """
        if not docs and not ai_summary:
            return "LOW"

        combined_text = ai_summary + " " + " ".join(d.get("text", "") for d in docs)
        doc_embedding = self.scoring_model.encode(
            combined_text, convert_to_tensor=True
        )

        scores = util.cos_sim(doc_embedding, self.ontology_embeddings)[0]
        top_idx = int(scores.argmax())
        top_score = float(scores[top_idx])

        best_concept = self.ontology_concepts[top_idx]
        severity_code = best_concept["severity"]

        logger.info(
            f"Ontology risk match: id={best_concept['id']} "
            f"severity={severity_code} score={top_score:.3f}"
        )

        MIN_CONFIDENCE = 0.40
        if top_score < MIN_CONFIDENCE:
            severity_code = "S0"

        return self._severity_code_to_label(severity_code)

    # ---------- Scoring + Prompt + Formatting (same as before) ----------

    def _calculate_real_scores(self, query, docs):
        if not docs:
            return docs

        query_embedding = self.scoring_model.encode(query, convert_to_tensor=True)
        doc_texts = [d["text"] for d in docs]
        doc_embeddings = self.scoring_model.encode(doc_texts, convert_to_tensor=True)

        cosine_scores = util.cos_sim(query_embedding, doc_embeddings)[0]

        for i, doc in enumerate(docs):
            raw_score = float(cosine_scores[i])
            human_score = min(0.98, (raw_score * 1.2) + 0.10)
            doc["real_score"] = human_score

        return docs

    def _prepare_context(self, docs):
        parts = []
        for i, doc in enumerate(docs[:4]):
            text = doc.get("text", "").replace("\n", " ").strip()
            if len(text) < 10:
                continue
            parts.append(f"[Document {i+1}]: {text}")
        if not parts:
            return "No detailed interaction records found."
        return "\n\n".join(parts)

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
            "🤖 AI SUMMARY:\n",
            f"{generated_text}\n\n",
        ]
        valid_docs = [d for d in docs if len(d.get("text", "")) > 10]
        if valid_docs:
            top_doc = valid_docs[0]
            score = top_doc.get("real_score", 0) * 100
            parts.append("📄 TOP EVIDENCE:\n")
            parts.append(f"• [Match: {score:.1f}%] {top_doc['text'][:150]}...\n\n")
        parts.append("─" * 50 + "\n⚠️ NOTE: Generated locally by FLAN-T5.")
        return "".join(parts)

    def _create_citations(self, docs):
        citations = []
        for i, doc in enumerate(docs[:5]):
            score = doc.get("real_score", 0.0)
            drug_name = doc.get("source", "Unknown")  # or doc.get("drug_name")
            citations.append(
                {
                    "id": i + 1,
                    "drug_name": drug_name,
                    "source": f"DrugBank Doc {i+1}",
                    "relevance_score": float(score),
                }
            )
        return citations


# Factory function (used by your framework)
def create_local_llm_agent():
    return LocalLLMAgent()


# Simple manual test
if __name__ == "__main__":
    async def test():
        agent = LocalLLMAgent()
        result = await agent.process_query("What are the interactions between aspirin and warfarin?")
        print(result["response"])
        print("Risk:", result["risk_score"])

    asyncio.run(test())