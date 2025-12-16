import logging
from typing import List, Dict, Optional
import torch
from transformers import pipeline, AutoTokenizer
from data_processor_drugbank import get_processor

logger = logging.getLogger(__name__)

class LocalRetrievalAgent:
    """
    Agent that retrieves documents using local FAISS index.
    """
    def __init__(self):
        self.processor = get_processor()
        
    def retrieve(self, query: str, top_k: int = 4) -> List[Dict]:
        logger.info(f"Retrieving documents for: {query}")
        return self.processor.search(query, top_k=top_k)

class LocalGenerationAgent:
    """
    Agent that generates responses using local FLAN-T5 model.
    No API keys required.
    """
    def __init__(self, model_name: str = "google/flan-t5-large"):
        logger.info(f"Loading local model: {model_name}...")
        
        # Detect hardware (Apple Silicon vs CUDA vs CPU)
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
            
        logger.info(f"Inference running on: {device.upper()}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            # We use a pipeline for easy text-to-text generation
            self.generator = pipeline(
                "text2text-generation",
                model=model_name,
                tokenizer=self.tokenizer,
                device=device if device != "mps" else -1, # MPS sometimes has issues with pipeline device indexing
                max_length=512
            )
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def generate(self, query: str, context_docs: List[Dict]) -> Dict:
        """Generate answer based on retrieved docs"""
        
        # 1. Prepare Context
        context_text = ""
        citations = []
        for i, doc in enumerate(context_docs[:3], 1):
            # Keep context concise for local model limits
            snippet = doc['text'].replace('\n', ' ').strip()[:300]
            context_text += f"[Doc {i}]: {snippet} "
            
            citations.append({
                'id': i,
                'source': doc.get('source', 'DrugBank'),
                'drug_name': doc.get('drug_name', 'Unknown'),
                'relevance_score': doc.get('relevance_score', 0.0)
            })

        # 2. Construct Prompt (Optimized for FLAN-T5)
        prompt = (
            f"Instruction: Answer the question strictly based on the Context below. "
            f"If the Context mentions a risk, specify it.\n\n"
            f"Context: {context_text}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )

        # 3. Generate
        try:
            output = self.generator(prompt, max_length=256, do_sample=False)
            response_text = output[0]['generated_text']
            
            # Simple rule-based risk scoring for local safety
            risk_score = self._calculate_risk(response_text + context_text)
            
            return {
                'response': response_text,
                'risk_score': risk_score,
                'citations': citations,
                'grounding_score': 0.85 # Placeholder for local
            }
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return {
                'response': "Error generating response locally.",
                'risk_score': "UNKNOWN",
                'citations': [],
                'grounding_score': 0.0
            }

    def _calculate_risk(self, text: str) -> str:
        text = text.lower()
        if any(x in text for x in ['fatal', 'life-threatening', 'severe', 'contraindicated']):
            return "HIGH"
        if any(x in text for x in ['monitor', 'caution', 'adjust', 'increase risk']):
            return "MODERATE"
        return "LOW"

class GroundedRAGSystem:
    """
    Main Local RAG System Entry Point.
    Replaces the API-based system with the local agents.
    """
    def __init__(self, api_key: Optional[str] = None):
        # API Key is accepted but IGNORED for local mode
        logger.info("Initializing Local Grounded RAG System...")
        self.retriever = LocalRetrievalAgent()
        self.generator = LocalGenerationAgent()

    async def process_query(self, query: str) -> Dict:
        # 1. Retrieve
        docs = self.retriever.retrieve(query)
        
        # 2. Generate
        # (Note: Local model calls are synchronous, but we keep async def for API compatibility)
        result = self.generator.generate(query, docs)
        
        # 3. Format result
        result['sub_queries'] = [query] # No decomposition in local mode
        result['num_retrieved_docs'] = len(docs)
        
        return result