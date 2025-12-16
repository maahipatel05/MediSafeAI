"""
Cross-Encoder Re-Ranker for Improved Retrieval
Uses a more powerful model to re-score initial retrieval results
"""

import logging
from typing import List, Dict
import numpy as np
from sentence_transformers import CrossEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DrugInteractionReRanker:
    """Re-rank retrieved documents using cross-encoder"""
    
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize cross-encoder for re-ranking
        
        Cross-encoder directly scores (query, document) pairs
        More accurate than bi-encoder but slower
        """
        logger.info(f"Loading cross-encoder: {model_name}")
        self.model = CrossEncoder(model_name)
        logger.info("Cross-encoder loaded successfully")
    
    def rerank(self, query: str, documents: List[Dict], top_k: int = None) -> List[Dict]:
        """
        Re-rank documents using cross-encoder
        
        Args:
            query: User's search query
            documents: Initial retrieval results from bi-encoder
            top_k: Number of documents to return (default: same as input)
        
        Returns:
            Re-ranked documents with updated relevance scores
        """
        if not documents:
            return documents
        
        if top_k is None:
            top_k = len(documents)
        
        logger.info(f"Re-ranking {len(documents)} documents for query: '{query[:50]}...'")
        
        # Prepare (query, document) pairs
        pairs = []
        for doc in documents:
            # Use the text field for scoring
            doc_text = doc.get('text', '')
            pairs.append([query, doc_text])
        
        # Score all pairs
        scores = self.model.predict(pairs)
        
        # Normalize scores to 0-1 range
        scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-8)
        
        # Update documents with new scores
        reranked_docs = []
        for doc, score in zip(documents, scores):
            doc_copy = doc.copy()
            doc_copy['original_score'] = doc.get('relevance_score', 0.0)
            doc_copy['reranker_score'] = float(score)
            doc_copy['relevance_score'] = float(score)  # Update main score
            reranked_docs.append(doc_copy)
        
        # Sort by new scores
        reranked_docs.sort(key=lambda x: x['reranker_score'], reverse=True)
        
        # Return top-k
        result = reranked_docs[:top_k]
        
        logger.info(f"Re-ranking complete. Score improvements:")
        for i, doc in enumerate(result[:3]):
            drug_name = doc.get('drug_name', 'Unknown')
            orig_score = doc.get('original_score', 0.0)
            new_score = doc.get('reranker_score', 0.0)
            logger.info(f"  {i+1}. {drug_name}: {orig_score:.3f} → {new_score:.3f}")
        
        return result
    
    def batch_rerank(self, queries: List[str], documents_list: List[List[Dict]], top_k: int = 5) -> List[List[Dict]]:
        """Re-rank multiple queries at once"""
        
        results = []
        for query, documents in zip(queries, documents_list):
            reranked = self.rerank(query, documents, top_k)
            results.append(reranked)
        
        return results


class HybridRetrieval:
    """Combine bi-encoder (fast) + cross-encoder (accurate)"""
    
    def __init__(self, bi_encoder_retriever, reranker: DrugInteractionReRanker):
        self.bi_encoder = bi_encoder_retriever
        self.reranker = reranker
    
    def retrieve(self, query: str, initial_k: int = 20, final_k: int = 5) -> List[Dict]:
        """
        Two-stage retrieval:
        1. Bi-encoder: Fast retrieval of top-20
        2. Cross-encoder: Accurate re-ranking to top-5
        
        This balances speed and accuracy
        """
        
        # Stage 1: Fast bi-encoder retrieval
        logger.info(f"Stage 1: Bi-encoder retrieval (top-{initial_k})")
        initial_results = self.bi_encoder.search(query, top_k=initial_k)
        
        # Stage 2: Accurate cross-encoder re-ranking
        logger.info(f"Stage 2: Cross-encoder re-ranking (top-{final_k})")
        final_results = self.reranker.rerank(query, initial_results, top_k=final_k)
        
        return final_results
    
    def retrieve_multi_query(self, queries: List[str], initial_k: int = 20, final_k: int = 5) -> List[Dict]:
        """Handle multiple sub-queries and merge results"""
        
        all_results = []
        seen_ids = set()
        
        for query in queries:
            results = self.retrieve(query, initial_k=initial_k, final_k=final_k)
            
            for doc in results:
                doc_id = doc.get('id', '')
                if doc_id not in seen_ids:
                    all_results.append(doc)
                    seen_ids.add(doc_id)
        
        # Sort by score and take top final_k
        all_results.sort(key=lambda x: x.get('relevance_score', 0.0), reverse=True)
        
        return all_results[:final_k]


# Example usage
if __name__ == '__main__':
    # Test re-ranker
    reranker = DrugInteractionReRanker()
    
    # Mock documents
    test_docs = [
        {
            'id': '1',
            'drug_name': 'Aspirin',
            'text': 'Aspirin is an antiplatelet drug used to reduce blood clotting.',
            'relevance_score': 0.7
        },
        {
            'id': '2',
            'drug_name': 'Warfarin',
            'text': 'Warfarin is an anticoagulant medication that prevents blood clots.',
            'relevance_score': 0.65
        },
        {
            'id': '3',
            'drug_name': 'Ibuprofen',
            'text': 'Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID).',
            'relevance_score': 0.8
        }
    ]
    
    query = "What is the interaction between aspirin and warfarin?"
    
    reranked = reranker.rerank(query, test_docs, top_k=3)
    
    print("\n=== Re-ranking Results ===")
    for i, doc in enumerate(reranked):
        print(f"{i+1}. {doc['drug_name']}")
        print(f"   Original score: {doc['original_score']:.3f}")
        print(f"   Re-ranker score: {doc['reranker_score']:.3f}")
