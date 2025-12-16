"""
Retrieval-Only Evaluation (No LLM Required)
Tests FAISS retrieval quality without needing Gemini API
"""

import json
import logging
from datetime import datetime
from evaluation import GroundTruthDataset, RAGEvaluator
from data_processor_drugbank import get_processor
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrievalOnlyEvaluator:
    """Evaluate retrieval performance without LLM generation"""
    
    def __init__(self):
        self.processor = get_processor()
        self.ground_truth = GroundTruthDataset()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def evaluate_retrieval(self):
        """Test retrieval quality on ground truth examples"""
        
        logger.info("=" * 80)
        logger.info("RETRIEVAL-ONLY EVALUATION (No LLM Calls)")
        logger.info("=" * 80)
        
        examples = self.ground_truth.get_examples()
        logger.info(f"\nTesting on {len(examples)} ground truth examples")
        
        results = {
            'precision_at_5': [],
            'recall_at_5': [],
            'ndcg_at_5': [],
            'mrr': [],
            'examples': []
        }
        
        for i, example in enumerate(examples, 1):
            query = example['query']
            expected_drugs = [d.lower() for d in example['expected_drugs']]
            
            logger.info(f"\n[{i}/{len(examples)}] Query: {query[:60]}...")
            logger.info(f"  Expected drugs: {expected_drugs}")
            
            # Retrieve documents
            retrieved_docs = self.processor.search(query, top_k=5)
            
            # Check which retrieved docs are relevant
            relevant_positions = []
            retrieved_texts = []
            
            for pos, doc in enumerate(retrieved_docs, 1):
                doc_text = doc.get('text', '').lower()
                retrieved_texts.append(doc_text[:100])
                
                # Check if any expected drug is in this document
                is_relevant = any(drug in doc_text for drug in expected_drugs)
                if is_relevant:
                    relevant_positions.append(pos)
            
            # Calculate metrics
            num_relevant_retrieved = len(relevant_positions)
            precision = num_relevant_retrieved / 5 if retrieved_docs else 0
            
            # Recall (assuming we want at least 1 relevant doc per expected drug category)
            recall = min(num_relevant_retrieved / len(expected_drugs), 1.0)
            
            # NDCG@5
            dcg = sum(1 / np.log2(pos + 1) for pos in relevant_positions)
            ideal_dcg = sum(1 / np.log2(i + 2) for i in range(min(num_relevant_retrieved, 5)))
            ndcg = dcg / ideal_dcg if ideal_dcg > 0 else 0
            
            # MRR (Mean Reciprocal Rank)
            mrr = 1 / relevant_positions[0] if relevant_positions else 0
            
            results['precision_at_5'].append(precision)
            results['recall_at_5'].append(recall)
            results['ndcg_at_5'].append(ndcg)
            results['mrr'].append(mrr)
            
            logger.info(f"  Retrieved {num_relevant_retrieved}/5 relevant docs")
            logger.info(f"  Precision@5: {precision:.3f}, Recall@5: {recall:.3f}, NDCG@5: {ndcg:.3f}, MRR: {mrr:.3f}")
            
            results['examples'].append({
                'query': query,
                'expected_drugs': expected_drugs,
                'relevant_retrieved': num_relevant_retrieved,
                'precision': precision,
                'recall': recall,
                'ndcg': ndcg,
                'mrr': mrr
            })
        
        # Calculate averages
        avg_results = {
            'retrieval': {
                'precision@5': np.mean(results['precision_at_5']),
                'recall@5': np.mean(results['recall_at_5']),
                'ndcg@5': np.mean(results['ndcg_at_5']),
                'mrr': np.mean(results['mrr'])
            },
            'timestamp': self.timestamp,
            'num_examples': len(examples),
            'details': results['examples']
        }
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("RETRIEVAL EVALUATION RESULTS")
        logger.info("=" * 80)
        logger.info(f"\nAverage Metrics (over {len(examples)} examples):")
        logger.info(f"  Precision@5: {avg_results['retrieval']['precision@5']:.4f} ({avg_results['retrieval']['precision@5']*100:.1f}%)")
        logger.info(f"  Recall@5:    {avg_results['retrieval']['recall@5']:.4f} ({avg_results['retrieval']['recall@5']*100:.1f}%)")
        logger.info(f"  NDCG@5:      {avg_results['retrieval']['ndcg@5']:.4f} ({avg_results['retrieval']['ndcg@5']*100:.1f}%)")
        logger.info(f"  MRR:         {avg_results['retrieval']['mrr']:.4f} ({avg_results['retrieval']['mrr']*100:.1f}%)")
        
        # Save results
        output_file = f'./results/retrieval_only_results_{self.timestamp}.json'
        with open(output_file, 'w') as f:
            json.dump(avg_results, f, indent=2)
        
        logger.info(f"\n✅ Results saved to: {output_file}")
        logger.info("=" * 80)
        
        return avg_results


if __name__ == '__main__':
    evaluator = RetrievalOnlyEvaluator()
    results = evaluator.evaluate_retrieval()
