"""
Comprehensive Evaluation Framework for Drug Interaction RAG System
Implements multiple metrics for retrieval and generation quality
"""

import json
import logging
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroundTruthDataset:
    """Ground truth test dataset for evaluation"""
    
    def __init__(self):
        self.examples = self.create_ground_truth()
    
    def create_ground_truth(self) -> List[Dict]:
        """
        Create ground truth examples with expected outputs
        These would ideally come from expert pharmacists
        """
        
        examples = [
            {
                'query': 'What are the interactions between aspirin and warfarin?',
                'expected_drugs': ['aspirin', 'warfarin', 'acetylsalicylic acid'],
                'expected_risk': 'HIGH',
                'has_interaction': True,
                'severity': 'major',
                'expected_keywords': ['bleeding', 'anticoagulant', 'antiplatelet', 'hemorrhage']
            },
            {
                'query': 'Can I take ibuprofen with blood pressure medication?',
                'expected_drugs': ['ibuprofen', 'antihypertensive', 'nsaid'],
                'expected_risk': 'MODERATE',
                'has_interaction': True,
                'severity': 'moderate',
                'expected_keywords': ['blood pressure', 'reduce effectiveness', 'kidney']
            },
            {
                'query': 'Is it safe to combine metformin with insulin?',
                'expected_drugs': ['metformin', 'insulin'],
                'expected_risk': 'LOW',
                'has_interaction': True,
                'severity': 'minor',
                'expected_keywords': ['diabetes', 'blood sugar', 'hypoglycemia']
            },
            {
                'query': 'What happens if I mix alcohol with antibiotics?',
                'expected_drugs': ['alcohol', 'antibiotic'],
                'expected_risk': 'MODERATE',
                'has_interaction': True,
                'severity': 'moderate',
                'expected_keywords': ['nausea', 'vomiting', 'reduce effectiveness']
            },
            {
                'query': 'Can I take vitamin C with aspirin?',
                'expected_drugs': ['vitamin c', 'ascorbic acid', 'aspirin'],
                'expected_risk': 'LOW',
                'has_interaction': False,
                'severity': 'minor',
                'expected_keywords': ['minimal', 'safe', 'low risk']
            },
            # Add more examples for robust evaluation
            {
                'query': 'Interaction between SSRIs and NSAIDs?',
                'expected_drugs': ['ssri', 'nsaid', 'selective serotonin reuptake inhibitor'],
                'expected_risk': 'MODERATE',
                'has_interaction': True,
                'severity': 'moderate',
                'expected_keywords': ['bleeding', 'gastrointestinal', 'serotonin']
            },
            {
                'query': 'Is grapefruit juice safe with statins?',
                'expected_drugs': ['grapefruit', 'statin', 'atorvastatin', 'simvastatin'],
                'expected_risk': 'HIGH',
                'has_interaction': True,
                'severity': 'major',
                'expected_keywords': ['increase', 'concentration', 'toxicity', 'muscle']
            },
            {
                'query': 'Can I take acetaminophen with ibuprofen?',
                'expected_drugs': ['acetaminophen', 'paracetamol', 'ibuprofen'],
                'expected_risk': 'LOW',
                'has_interaction': False,
                'severity': 'minor',
                'expected_keywords': ['safe', 'different', 'mechanism']
            }
        ]
        
        return examples
    
    def get_examples(self) -> List[Dict]:
        return self.examples
    
    def save_to_file(self, path: str = './data/ground_truth.json'):
        """Save ground truth to file"""
        with open(path, 'w') as f:
            json.dump(self.examples, f, indent=2)
        logger.info(f"Saved {len(self.examples)} ground truth examples to {path}")


class RetrievalMetrics:
    """Metrics for evaluating retrieval quality"""
    
    @staticmethod
    def precision_at_k(retrieved: List[Dict], expected_drugs: List[str], k: int = 5) -> float:
        """
        Precision@K: What fraction of top-K results are relevant?
        """
        retrieved_k = retrieved[:k]
        relevant_count = 0
        
        for doc in retrieved_k:
            drug_name = doc.get('drug_name', '').lower()
            interacting_drug = doc.get('interacting_drug', '').lower()
            
            # Check if any expected drug matches
            for expected in expected_drugs:
                expected = expected.lower()
                if expected in drug_name or expected in interacting_drug:
                    relevant_count += 1
                    break
        
        return relevant_count / k if k > 0 else 0.0
    
    @staticmethod
    def recall_at_k(retrieved: List[Dict], expected_drugs: List[str], k: int = 5) -> float:
        """
        Recall@K: What fraction of relevant items are in top-K?
        """
        retrieved_k = retrieved[:k]
        found_drugs = set()
        
        for doc in retrieved_k:
            drug_name = doc.get('drug_name', '').lower()
            interacting_drug = doc.get('interacting_drug', '').lower()
            
            for expected in expected_drugs:
                expected = expected.lower()
                if expected in drug_name or expected in interacting_drug:
                    found_drugs.add(expected)
        
        return len(found_drugs) / len(expected_drugs) if len(expected_drugs) > 0 else 0.0
    
    @staticmethod
    def ndcg_at_k(retrieved: List[Dict], expected_drugs: List[str], k: int = 5) -> float:
        """
        Normalized Discounted Cumulative Gain@K
        Rewards relevant documents ranked higher
        """
        retrieved_k = retrieved[:k]
        
        # Calculate DCG
        dcg = 0.0
        for i, doc in enumerate(retrieved_k):
            drug_name = doc.get('drug_name', '').lower()
            interacting_drug = doc.get('interacting_drug', '').lower()
            
            # Check relevance (1 if relevant, 0 otherwise)
            relevance = 0
            for expected in expected_drugs:
                expected = expected.lower()
                if expected in drug_name or expected in interacting_drug:
                    relevance = 1
                    break
            
            # DCG formula: sum(rel_i / log2(i+2))
            dcg += relevance / np.log2(i + 2)
        
        # Calculate Ideal DCG (all relevant docs at top)
        ideal_relevances = [1] * min(len(expected_drugs), k) + [0] * (k - len(expected_drugs))
        idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_relevances))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def mean_reciprocal_rank(retrieved: List[Dict], expected_drugs: List[str]) -> float:
        """
        MRR: Reciprocal of rank of first relevant document
        """
        for i, doc in enumerate(retrieved):
            drug_name = doc.get('drug_name', '').lower()
            interacting_drug = doc.get('interacting_drug', '').lower()
            
            for expected in expected_drugs:
                expected = expected.lower()
                if expected in drug_name or expected in interacting_drug:
                    return 1.0 / (i + 1)
        
        return 0.0


class GenerationMetrics:
    """Metrics for evaluating generation quality"""
    
    @staticmethod
    def risk_accuracy(predicted_risk: str, expected_risk: str) -> float:
        """Exact match on risk level"""
        return 1.0 if predicted_risk.upper() == expected_risk.upper() else 0.0
    
    @staticmethod
    def risk_mae(predicted_risk: str, expected_risk: str) -> float:
        """Mean Absolute Error on risk levels (treating as ordinal)"""
        risk_levels = {'LOW': 0, 'MODERATE': 1, 'HIGH': 2, 'CRITICAL': 3}
        
        pred_level = risk_levels.get(predicted_risk.upper(), 1)
        exp_level = risk_levels.get(expected_risk.upper(), 1)
        
        return abs(pred_level - exp_level)
    
    @staticmethod
    def keyword_coverage(response: str, expected_keywords: List[str]) -> float:
        """What fraction of expected keywords appear in response?"""
        response_lower = response.lower()
        found_count = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
        return found_count / len(expected_keywords) if len(expected_keywords) > 0 else 0.0
    
    @staticmethod
    def citation_accuracy(citations: List[Dict], expected_drugs: List[str]) -> float:
        """Are cited drugs relevant to the query?"""
        cited_drugs = set()
        for citation in citations:
            drug_name = citation.get('drug_name', '').lower()
            cited_drugs.add(drug_name)
        
        relevant_citations = 0
        for cited in cited_drugs:
            for expected in expected_drugs:
                if expected.lower() in cited or cited in expected.lower():
                    relevant_citations += 1
                    break
        
        return relevant_citations / len(citations) if len(citations) > 0 else 0.0
    
    @staticmethod
    def response_length_score(response: str, min_words: int = 50, max_words: int = 300) -> float:
        """Penalize responses that are too short or too long"""
        word_count = len(response.split())
        
        if word_count < min_words:
            return word_count / min_words
        elif word_count > max_words:
            return max_words / word_count
        else:
            return 1.0


class RAGEvaluator:
    """Complete evaluation suite for RAG system"""
    
    def __init__(self, rag_system, ground_truth: GroundTruthDataset):
        self.rag_system = rag_system
        self.ground_truth = ground_truth
        self.retrieval_metrics = RetrievalMetrics()
        self.generation_metrics = GenerationMetrics()
    
    async def evaluate_retrieval(self) -> Dict[str, float]:
        """Evaluate retrieval component"""
        
        logger.info("Evaluating retrieval quality...")
        
        metrics = {
            'precision@5': [],
            'recall@5': [],
            'ndcg@5': [],
            'mrr': []
        }
        
        for example in self.ground_truth.get_examples():
            query = example['query']
            expected_drugs = example['expected_drugs']
            
            # Get retrieval results (without generation)
            sub_queries = await self.rag_system.query_agent.decompose(query)
            retrieved = await self.rag_system.retrieval_agent.retrieve(sub_queries, top_k=3)
            
            # Calculate metrics
            metrics['precision@5'].append(
                self.retrieval_metrics.precision_at_k(retrieved, expected_drugs, k=5)
            )
            metrics['recall@5'].append(
                self.retrieval_metrics.recall_at_k(retrieved, expected_drugs, k=5)
            )
            metrics['ndcg@5'].append(
                self.retrieval_metrics.ndcg_at_k(retrieved, expected_drugs, k=5)
            )
            metrics['mrr'].append(
                self.retrieval_metrics.mean_reciprocal_rank(retrieved, expected_drugs)
            )
        
        # Average metrics
        results = {key: np.mean(values) for key, values in metrics.items()}
        
        logger.info("Retrieval Evaluation Results:")
        for key, value in results.items():
            logger.info(f"  {key}: {value:.4f}")
        
        return results
    
    async def evaluate_generation(self) -> Dict[str, float]:
        """Evaluate generation component"""
        
        logger.info("Evaluating generation quality...")
        
        metrics = {
            'risk_accuracy': [],
            'risk_mae': [],
            'keyword_coverage': [],
            'citation_accuracy': [],
            'response_length': []
        }
        
        for example in self.ground_truth.get_examples():
            query = example['query']
            
            # Get full response
            result = await self.rag_system.process_query(query)
            
            # Calculate metrics
            metrics['risk_accuracy'].append(
                self.generation_metrics.risk_accuracy(
                    result['risk_score'], 
                    example['expected_risk']
                )
            )
            metrics['risk_mae'].append(
                self.generation_metrics.risk_mae(
                    result['risk_score'],
                    example['expected_risk']
                )
            )
            metrics['keyword_coverage'].append(
                self.generation_metrics.keyword_coverage(
                    result['response'],
                    example['expected_keywords']
                )
            )
            metrics['citation_accuracy'].append(
                self.generation_metrics.citation_accuracy(
                    result['citations'],
                    example['expected_drugs']
                )
            )
            metrics['response_length'].append(
                self.generation_metrics.response_length_score(result['response'])
            )
        
        # Average metrics
        results = {key: np.mean(values) for key, values in metrics.items()}
        
        logger.info("Generation Evaluation Results:")
        for key, value in results.items():
            logger.info(f"  {key}: {value:.4f}")
        
        return results
    
    async def evaluate_end_to_end(self) -> Dict[str, any]:
        """Complete end-to-end evaluation"""
        
        logger.info("=" * 60)
        logger.info("Starting Comprehensive Evaluation")
        logger.info("=" * 60)
        
        retrieval_results = await self.evaluate_retrieval()
        generation_results = await self.evaluate_generation()
        
        # Combined results
        results = {
            'retrieval': retrieval_results,
            'generation': generation_results,
            'overall_score': (
                np.mean(list(retrieval_results.values())) * 0.4 +
                np.mean(list(generation_results.values())) * 0.6
            )
        }
        
        logger.info("=" * 60)
        logger.info(f"Overall System Score: {results['overall_score']:.4f}")
        logger.info("=" * 60)
        
        return results
    
    def save_results(self, results: Dict, path: str = './evaluation_results.json'):
        """Save evaluation results to file"""
        with open(path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {path}")


# Example usage
if __name__ == '__main__':
    # Create ground truth
    ground_truth = GroundTruthDataset()
    ground_truth.save_to_file()
    
    logger.info(f"Created {len(ground_truth.get_examples())} ground truth examples")
