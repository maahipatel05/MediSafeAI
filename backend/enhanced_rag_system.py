"""
Enhanced RAG System with All Advanced Components
Integrates all improvements into a cohesive system
"""

import logging
from typing import List, Dict
from agents import GroundedRAGSystem
from reranker import DrugInteractionReRanker, HybridRetrieval
from uncertainty_hallucination import UncertaintyQuantifier, GroundingVerifier, ConfidenceScorer
from drug_interaction_graph import DrugInteractionGraph, GraphEnhancedRetrieval
from data_processor_drugbank import get_processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedRAGSystem(GroundedRAGSystem):
    """
    Enhanced RAG System with all advanced features:
    - Cross-encoder re-ranking
    - Uncertainty quantification  
    - Hallucination detection
    - Graph-based retrieval
    - Confidence scoring
    """
    
    def __init__(self, api_key: str, use_enhanced_features: bool = True):
        super().__init__(api_key)
        
        self.use_enhanced_features = use_enhanced_features
        
        if use_enhanced_features:
            logger.info("Initializing enhanced components...")
            
            # Get data processor
            self.processor = get_processor()
            
            # Initialize re-ranker
            self.reranker = DrugInteractionReRanker()
            
            # Initialize hybrid retrieval
            self.hybrid_retrieval = HybridRetrieval(
                self.processor,
                self.reranker
            )
            
            # Initialize uncertainty quantifier
            self.uncertainty_quantifier = UncertaintyQuantifier(self.generation_agent)
            
            # Initialize grounding verifier
            self.grounding_verifier = GroundingVerifier()
            
            # Initialize confidence scorer
            self.confidence_scorer = ConfidenceScorer()
            
            # Initialize drug interaction graph
            self.drug_graph = DrugInteractionGraph()
            logger.info("Building drug interaction graph...")
            self.drug_graph.build_from_drugbank(self.processor.chunks)
            
            # Initialize graph-enhanced retrieval
            self.graph_retrieval = GraphEnhancedRetrieval(
                self.drug_graph,
                self.processor
            )
            
            logger.info("✓ All enhanced components initialized")
    
    async def process_query_enhanced(self, 
                                    query: str,
                                    use_uncertainty: bool = True,
                                    use_reranking: bool = True,
                                    use_graph: bool = True,
                                    verify_grounding: bool = True) -> Dict:
        """
        Process query with all enhancements
        
        Pipeline:
        1. Query decomposition
        2. Graph-enhanced retrieval (optional)
        3. Cross-encoder re-ranking (optional)
        4. Generation with uncertainty (optional)
        5. Grounding verification (optional)
        6. Confidence scoring
        """
        
        logger.info("=" * 70)
        logger.info(f"Processing Enhanced Query: {query[:50]}...")
        logger.info("=" * 70)
        
        # Step 1: Query Decomposition
        logger.info("\n[1/6] Query Decomposition")
        sub_queries = await self.query_agent.decompose(query)
        logger.info(f"  Generated {len(sub_queries)} sub-queries")
        
        # Step 2: Retrieval
        logger.info("\n[2/6] Document Retrieval")
        
        if use_graph and self.use_enhanced_features:
            # Extract drug names from query (simple extraction)
            import re
            words = re.findall(r'\b[A-Z][a-z]+\b', query)
            query_drugs = [w for w in words if len(w) > 3]  # Simple heuristic
            
            if query_drugs:
                logger.info(f"  Using graph-enhanced retrieval for: {query_drugs}")
                retrieved_docs = self.graph_retrieval.retrieve_with_graph_expansion(
                    query, query_drugs, top_k=10
                )
            else:
                retrieved_docs = await self.retrieval_agent.retrieve(sub_queries, top_k=3)
        else:
            retrieved_docs = await self.retrieval_agent.retrieve(sub_queries, top_k=3)
        
        logger.info(f"  Retrieved {len(retrieved_docs)} documents")
        
        # Calculate retrieval uncertainty
        retrieval_uncertainty = None
        if self.use_enhanced_features:
            retrieval_uncertainty = self.uncertainty_quantifier.calculate_retrieval_uncertainty(
                retrieved_docs
            )
            logger.info(f"  Retrieval confidence: {retrieval_uncertainty.get('retrieval_confidence', 0):.3f}")
        
        # Step 3: Re-ranking
        logger.info("\n[3/6] Re-ranking")
        
        if use_reranking and self.use_enhanced_features:
            retrieved_docs = self.reranker.rerank(query, retrieved_docs, top_k=6)
            logger.info(f"  Re-ranked to top {len(retrieved_docs)} documents")
        
        # Step 4: Generation
        logger.info("\n[4/6] Response Generation")
        
        if use_uncertainty and self.use_enhanced_features:
            logger.info("  Using uncertainty quantification (5 samples)")
            result = await self.uncertainty_quantifier.predict_with_uncertainty(
                query, retrieved_docs, num_samples=3  # Reduced for speed
            )
        else:
            result = await self.generation_agent.generate(query, retrieved_docs)
        
        # Add metadata
        result['sub_queries'] = sub_queries
        result['num_retrieved_docs'] = len(retrieved_docs)
        
        # Step 5: Grounding Verification
        logger.info("\n[5/6] Grounding Verification")
        
        grounding_metrics = None
        if verify_grounding and self.use_enhanced_features:
            grounding_metrics = self.grounding_verifier.verify_response(
                result['response'],
                retrieved_docs
            )
            result['grounding_metrics'] = grounding_metrics
            result['grounding_score'] = grounding_metrics['grounding_score']
            result['hallucination_rate'] = grounding_metrics['hallucination_rate']
            
            logger.info(f"  Grounding score: {grounding_metrics['grounding_score']:.3f}")
            logger.info(f"  Hallucination rate: {grounding_metrics['hallucination_rate']:.3f}")
        
        # Step 6: Confidence Scoring
        logger.info("\n[6/6] Confidence Scoring")
        
        if self.use_enhanced_features:
            confidence_info = self.confidence_scorer.calculate_overall_confidence(
                result,
                retrieval_uncertainty,
                grounding_metrics
            )
            result['confidence_info'] = confidence_info
            
            logger.info(f"  Overall confidence: {confidence_info['overall_confidence']:.3f}")
            logger.info(f"  Confidence level: {confidence_info['confidence_level']}")
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ Enhanced Processing Complete")
        logger.info("=" * 70 + "\n")
        
        return result
    
    async def process_query(self, query: str) -> Dict:
        """
        Process query - delegates to enhanced version if enabled
        """
        if self.use_enhanced_features:
            return await self.process_query_enhanced(query)
        else:
            return await super().process_query(query)
    
    def get_system_info(self) -> Dict:
        """Get information about enabled features"""
        
        info = {
            'base_features': [
                'Query Decomposition',
                'Semantic Retrieval (FAISS)',
                'Grounded Generation (Gemini 2.5 Pro)'
            ]
        }
        
        if self.use_enhanced_features:
            info['enhanced_features'] = [
                'Cross-Encoder Re-Ranking',
                'Uncertainty Quantification',
                'Hallucination Detection',
                'Drug Interaction Graph',
                'Graph-Enhanced Retrieval',
                'Confidence Scoring'
            ]
            
            info['graph_stats'] = {
                'num_drugs': self.drug_graph.graph.number_of_nodes(),
                'num_interactions': self.drug_graph.graph.number_of_edges(),
                'graph_density': round(self.drug_graph.graph.density(), 4)
            }
        
        return info


# Factory function
def create_rag_system(api_key: str, enhanced: bool = True):
    """Create RAG system (enhanced or basic)"""
    
    if enhanced:
        logger.info("Creating Enhanced RAG System")
        return EnhancedRAGSystem(api_key, use_enhanced_features=True)
    else:
        logger.info("Creating Basic RAG System")
        return GroundedRAGSystem(api_key)


# Example usage
if __name__ == '__main__':
    import asyncio
    import os
    
    async def test_enhanced_system():
        api_key = os.environ.get('GEMINI_API_KEY')
        
        # Create enhanced system
        rag_system = create_rag_system(api_key, enhanced=True)
        
        # Get system info
        info = rag_system.get_system_info()
        print("\n=== System Information ===")
        print(f"Base Features: {', '.join(info['base_features'])}")
        if 'enhanced_features' in info:
            print(f"Enhanced Features: {', '.join(info['enhanced_features'])}")
            print(f"\nGraph Stats:")
            for key, value in info['graph_stats'].items():
                print(f"  {key}: {value}")
        
        # Test query
        test_query = "What are the interactions between aspirin and warfarin?"
        print(f"\n=== Testing Query ===")
        print(f"Query: {test_query}")
        
        result = await rag_system.process_query(test_query)
        
        print(f"\n=== Results ===")
        print(f"Risk Score: {result.get('risk_score')}")
        print(f"Grounding Score: {result.get('grounding_score', 0):.3f}")
        if 'confidence_info' in result:
            print(f"Confidence: {result['confidence_info']['overall_confidence']:.3f}")
            print(f"Confidence Level: {result['confidence_info']['confidence_level']}")
        
        print(f"\nResponse:\n{result.get('response')[:200]}...")
    
    # Run test
    asyncio.run(test_enhanced_system())
