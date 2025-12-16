"""
Baseline Methods for Comparison
Implements simpler retrieval methods to demonstrate improvement
"""

import logging
import re
from typing import List, Dict
from collections import Counter
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeywordSearchBaseline:
    """Simple keyword-based search (TF-IDF style)"""
    
    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks
        self.build_index()
    
    def build_index(self):
        """Build inverted index for keyword search"""
        self.inverted_index = {}
        
        for idx, chunk in enumerate(self.chunks):
            text = chunk.get('text', '').lower()
            words = re.findall(r'\w+', text)
            
            for word in set(words):
                if word not in self.inverted_index:
                    self.inverted_index[word] = []
                self.inverted_index[word].append(idx)
        
        logger.info(f"Built keyword index with {len(self.inverted_index)} terms")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Simple keyword matching"""
        query_words = set(re.findall(r'\w+', query.lower()))
        
        # Count matches for each document
        doc_scores = Counter()
        for word in query_words:
            if word in self.inverted_index:
                for doc_idx in self.inverted_index[word]:
                    doc_scores[doc_idx] += 1
        
        # Get top-k documents
        top_docs = doc_scores.most_common(top_k)
        
        results = []
        for doc_idx, score in top_docs:
            doc = self.chunks[doc_idx].copy()
            doc['relevance_score'] = score / len(query_words) if query_words else 0
            results.append(doc)
        
        return results


class BM25Baseline:
    """BM25 ranking algorithm - standard IR baseline"""
    
    def __init__(self, chunks: List[Dict], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.build_index()
    
    def build_index(self):
        """Build BM25 index"""
        self.doc_freqs = {}
        self.doc_lengths = []
        self.doc_term_freqs = []
        
        # Calculate document frequencies and term frequencies
        for chunk in self.chunks:
            text = chunk.get('text', '').lower()
            words = re.findall(r'\w+', text)
            
            self.doc_lengths.append(len(words))
            
            # Term frequencies in this document
            term_freq = Counter(words)
            self.doc_term_freqs.append(term_freq)
            
            # Document frequencies (how many docs contain each term)
            for word in set(words):
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1
        
        self.avgdl = np.mean(self.doc_lengths) if self.doc_lengths else 0
        logger.info(f"Built BM25 index: {len(self.chunks)} docs, avg length: {self.avgdl:.2f}")
    
    def idf(self, term: str) -> float:
        """Inverse document frequency"""
        N = len(self.chunks)
        df = self.doc_freqs.get(term, 0)
        return np.log((N - df + 0.5) / (df + 0.5) + 1.0)
    
    def score(self, query: str, doc_idx: int) -> float:
        """BM25 score for a query-document pair"""
        query_words = re.findall(r'\w+', query.lower())
        
        score = 0.0
        doc_length = self.doc_lengths[doc_idx]
        term_freqs = self.doc_term_freqs[doc_idx]
        
        for term in query_words:
            if term in term_freqs:
                tf = term_freqs[term]
                idf = self.idf(term)
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avgdl))
                score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve documents using BM25"""
        scores = []
        for idx in range(len(self.chunks)):
            score = self.score(query, idx)
            scores.append((idx, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k
        results = []
        for idx, score in scores[:top_k]:
            doc = self.chunks[idx].copy()
            doc['relevance_score'] = float(score)
            results.append(doc)
        
        return results


class NoDecompositionBaseline:
    """RAG without query decomposition"""
    
    def __init__(self, processor):
        self.processor = processor
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Direct search without breaking down query"""
        return self.processor.search(query, top_k=top_k)


class RandomBaseline:
    """Random retrieval (worst case baseline)"""
    
    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Return random documents"""
        import random
        selected = random.sample(self.chunks, min(top_k, len(self.chunks)))
        for doc in selected:
            doc['relevance_score'] = random.random()
        return selected


class BaselineComparator:
    """Compare all baselines against main system"""
    
    def __init__(self, chunks: List[Dict], main_system):
        self.chunks = chunks
        self.main_system = main_system
        
        # Initialize baselines
        logger.info("Initializing baselines...")
        self.baselines = {
            'Keyword Search': KeywordSearchBaseline(chunks),
            'BM25': BM25Baseline(chunks),
            'No Decomposition': NoDecompositionBaseline(main_system),
            'Random': RandomBaseline(chunks)
        }
        logger.info(f"Initialized {len(self.baselines)} baseline methods")
    
    async def compare_retrievals(self, query: str, expected_drugs: List[str], top_k: int = 5) -> Dict:
        """Compare all methods on a single query"""
        
        results = {}
        
        # Main system (with decomposition)
        logger.info(f"Testing main system on: '{query[:50]}...'")
        sub_queries = await self.main_system.query_agent.decompose(query)
        main_results = await self.main_system.retrieval_agent.retrieve(sub_queries, top_k=3)
        results['Main System (RAG)'] = main_results
        
        # Baselines
        for name, baseline in self.baselines.items():
            logger.info(f"Testing {name}...")
            baseline_results = baseline.search(query, top_k=top_k)
            results[name] = baseline_results
        
        # Calculate precision for each
        from evaluation import RetrievalMetrics
        metrics = RetrievalMetrics()
        
        comparison = {}
        for name, retrieved in results.items():
            precision = metrics.precision_at_k(retrieved, expected_drugs, k=top_k)
            recall = metrics.recall_at_k(retrieved, expected_drugs, k=top_k)
            ndcg = metrics.ndcg_at_k(retrieved, expected_drugs, k=top_k)
            
            comparison[name] = {
                'precision@5': precision,
                'recall@5': recall,
                'ndcg@5': ndcg,
                'f1': 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            }
        
        return comparison
    
    async def evaluate_all_baselines(self, ground_truth_examples: List[Dict]) -> Dict:
        """Evaluate all methods on ground truth dataset"""
        
        logger.info("=" * 60)
        logger.info("Baseline Comparison Evaluation")
        logger.info("=" * 60)
        
        all_results = {name: {'precision@5': [], 'recall@5': [], 'ndcg@5': [], 'f1': []} 
                      for name in ['Main System (RAG)'] + list(self.baselines.keys())}
        
        for i, example in enumerate(ground_truth_examples):
            logger.info(f"\nQuery {i+1}/{len(ground_truth_examples)}: {example['query'][:50]}...")
            
            comparison = await self.compare_retrievals(
                example['query'], 
                example['expected_drugs'],
                top_k=5
            )
            
            for method_name, metrics in comparison.items():
                for metric_name, value in metrics.items():
                    all_results[method_name][metric_name].append(value)
        
        # Average results
        final_results = {}
        for method_name, metrics in all_results.items():
            final_results[method_name] = {
                metric: np.mean(values) for metric, values in metrics.items()
            }
        
        # Print comparison table
        logger.info("\n" + "=" * 80)
        logger.info("BASELINE COMPARISON RESULTS")
        logger.info("=" * 80)
        logger.info(f"{'Method':<25} {'Precision@5':<15} {'Recall@5':<15} {'NDCG@5':<15} {'F1':<10}")
        logger.info("-" * 80)
        
        for method_name in sorted(final_results.keys(), key=lambda x: final_results[x]['f1'], reverse=True):
            metrics = final_results[method_name]
            logger.info(
                f"{method_name:<25} "
                f"{metrics['precision@5']:<15.4f} "
                f"{metrics['recall@5']:<15.4f} "
                f"{metrics['ndcg@5']:<15.4f} "
                f"{metrics['f1']:<10.4f}"
            )
        
        logger.info("=" * 80)
        
        return final_results
    
    def save_comparison(self, results: Dict, path: str = './baseline_comparison.json'):
        """Save comparison results"""
        import json
        with open(path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Baseline comparison saved to {path}")


# Example usage
if __name__ == '__main__':
    # Test individual baselines
    test_chunks = [
        {'id': '1', 'drug_name': 'Aspirin', 'text': 'Aspirin is an antiplatelet drug that prevents blood clotting.'},
        {'id': '2', 'drug_name': 'Warfarin', 'text': 'Warfarin is an anticoagulant used to prevent blood clots.'},
        {'id': '3', 'drug_name': 'Ibuprofen', 'text': 'Ibuprofen is an NSAID used for pain and inflammation.'},
    ]
    
    # Test keyword search
    keyword_baseline = KeywordSearchBaseline(test_chunks)
    results = keyword_baseline.search("aspirin warfarin interaction", top_k=2)
    
    print("\nKeyword Search Results:")
    for doc in results:
        print(f"  - {doc['drug_name']}: {doc['relevance_score']:.3f}")
    
    # Test BM25
    bm25_baseline = BM25Baseline(test_chunks)
    results = bm25_baseline.search("aspirin warfarin interaction", top_k=2)
    
    print("\nBM25 Results:")
    for doc in results:
        print(f"  - {doc['drug_name']}: {doc['relevance_score']:.3f}")
