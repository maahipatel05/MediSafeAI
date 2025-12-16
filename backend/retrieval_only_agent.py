"""
Retrieval-Only Agent (No LLM API Required)
Uses only SentenceTransformer + FAISS for document retrieval
"""

from data_processor_drugbank import get_processor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrievalOnlyAgent:
    """
    Simple agent that uses only FAISS retrieval without LLM generation.
    No API keys needed - fully local processing.
    """
    
    def __init__(self):
        self.processor = get_processor()
        logger.info("RetrievalOnlyAgent initialized with SentenceTransformer")
    
    def process_query(self, query: str, top_k: int = 5):
        """
        Process query using only FAISS retrieval (no LLM)
        
        Args:
            query: User's drug interaction question
            top_k: Number of documents to retrieve
            
        Returns:
            dict with retrieved documents and risk assessment
        """
        logger.info(f"Processing query (retrieval-only): {query}")
        
        # Retrieve relevant documents using SentenceTransformer + FAISS
        retrieved_docs = self.processor.search(query, top_k=top_k)
        
        # Simple rule-based risk assessment
        risk_score = self._assess_risk(retrieved_docs, query)
        
        # Format response
        response = self._format_response(query, retrieved_docs, risk_score)
        
        return {
            'query': query,
            'response': response,
            'risk_score': risk_score,
            'citations': [
                {
                    'source': f"DrugBank Document {i+1}",
                    'text': doc['text'][:200] + "...",
                    'relevance_score': doc.get('score', 0.0)
                }
                for i, doc in enumerate(retrieved_docs)
            ],
            'num_docs': len(retrieved_docs),
            'method': 'retrieval_only',
            'note': 'This response is based purely on retrieved documents without LLM generation.'
        }
    
    def _assess_risk(self, docs, query):
        """Simple rule-based risk assessment from retrieved documents"""
        
        # Keywords indicating high risk
        high_risk_keywords = [
            'bleeding', 'hemorrhage', 'contraindicated', 'severe', 'fatal',
            'dangerous', 'toxic', 'overdose', 'emergency', 'critical'
        ]
        
        # Keywords indicating moderate risk
        moderate_risk_keywords = [
            'caution', 'monitor', 'adjust', 'increase', 'decrease',
            'may cause', 'potential', 'interaction', 'affect'
        ]
        
        # Keywords indicating low risk
        low_risk_keywords = [
            'minor', 'unlikely', 'safe', 'no significant', 'well-tolerated'
        ]
        
        # Combine all document text
        all_text = ' '.join([doc['text'].lower() for doc in docs])
        
        # Count keyword occurrences
        high_count = sum(keyword in all_text for keyword in high_risk_keywords)
        moderate_count = sum(keyword in all_text for keyword in moderate_risk_keywords)
        low_count = sum(keyword in all_text for keyword in low_risk_keywords)
        
        # Determine risk level
        if high_count >= 2:
            return 'HIGH'
        elif moderate_count >= 2:
            return 'MODERATE'
        elif low_count >= 1:
            return 'LOW'
        else:
            return 'MODERATE'  # Default
    
    def _format_response(self, query, docs, risk_score):
        """Format retrieved documents into a readable response"""
        
        if not docs:
            return "No relevant drug information found in the database. Please consult a healthcare professional."
        
        # Build response from retrieved documents
        response_parts = []
        
        # Header
        response_parts.append(f"**Drug Interaction Information** (Risk Level: {risk_score})\n")
        response_parts.append("Based on retrieved DrugBank documents:\n\n")
        
        # Add relevant excerpts from top documents
        for i, doc in enumerate(docs[:3], 1):
            text = doc['text']
            # Extract first 300 characters
            excerpt = text[:300].strip()
            if len(text) > 300:
                excerpt += "..."
            
            response_parts.append(f"**Source {i}:**\n{excerpt}\n\n")
        
        # Footer
        response_parts.append("⚠️ **Important:** This information is retrieved directly from DrugBank database. ")
        response_parts.append("Always consult a healthcare professional before making medication decisions.\n\n")
        response_parts.append("**Note:** This response was generated using document retrieval only (no LLM). ")
        response_parts.append("For more comprehensive analysis, API quota is needed.")
        
        return ''.join(response_parts)


# Helper function for easy integration
def create_retrieval_only_agent():
    """Create a retrieval-only agent instance"""
    return RetrievalOnlyAgent()


if __name__ == '__main__':
    # Test the agent
    agent = RetrievalOnlyAgent()
    
    test_queries = [
        "What are the interactions between aspirin and warfarin?",
        "Can I take metformin with insulin?",
        "Is grapefruit juice safe with statins?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        
        result = agent.process_query(query)
        
        print(f"\nRisk Score: {result['risk_score']}")
        print(f"Documents Retrieved: {result['num_docs']}")
        print(f"\nResponse:\n{result['response'][:500]}...")
        print(f"\nCitations: {len(result['citations'])} sources")
