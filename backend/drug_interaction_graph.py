"""
Drug Interaction Graph - Novel Architecture Component
Uses graph structure to improve retrieval and reasoning
"""

import logging
import networkx as nx
import json
from typing import List, Dict, Set, Tuple
import numpy as np
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DrugInteractionGraph:
    """
    Graph-based representation of drug interactions
    Nodes: Drugs
    Edges: Interactions (weighted by severity)
    """
    
    def __init__(self):
        self.graph = nx.Graph()
        self.drug_attributes = {}
        self.interaction_severity_map = {
            'minor': 1,
            'moderate': 2,
            'major': 3,
            'contraindicated': 4
        }
    
    def build_from_drugbank(self, chunks: List[Dict]):
        """Build graph from DrugBank chunks"""
        
        logger.info("Building drug interaction graph...")
        
        # Add nodes (drugs)
        drug_chunks = [c for c in chunks if 'interacting_drug' not in c]
        for chunk in drug_chunks:
            drug_name = chunk.get('drug_name', '')
            if drug_name:
                self.graph.add_node(drug_name)
                self.drug_attributes[drug_name] = {
                    'description': chunk.get('description', ''),
                    'categories': chunk.get('categories', []),
                    'toxicity': chunk.get('toxicity', '')
                }
        
        logger.info(f"Added {self.graph.number_of_nodes()} drug nodes")
        
        # Add edges (interactions)
        interaction_chunks = [c for c in chunks if 'interacting_drug' in c]
        edge_count = 0
        
        for chunk in interaction_chunks:
            drug_a = chunk.get('drug_name', '')
            drug_b = chunk.get('interacting_drug', '')
            interaction_desc = chunk.get('interaction_description', '')
            
            if drug_a and drug_b:
                # Infer severity from description
                severity = self._infer_severity(interaction_desc)
                weight = self.interaction_severity_map.get(severity, 2)
                
                self.graph.add_edge(
                    drug_a, 
                    drug_b,
                    weight=weight,
                    severity=severity,
                    description=interaction_desc
                )
                edge_count += 1
        
        logger.info(f"Added {edge_count} interaction edges")
        logger.info(f"Graph density: {nx.density(self.graph):.4f}")
        
        return self.graph
    
    def _infer_severity(self, description: str) -> str:
        """Infer interaction severity from description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['contraindicated', 'fatal', 'life-threatening', 'severe']):
            return 'contraindicated'
        elif any(word in desc_lower for word in ['major', 'serious', 'significant']):
            return 'major'
        elif any(word in desc_lower for word in ['moderate', 'caution', 'monitor']):
            return 'moderate'
        else:
            return 'minor'
    
    def get_drug_neighbors(self, drug_name: str, max_hops: int = 2) -> Dict[str, List[str]]:
        """Get drugs that interact with given drug"""
        
        if drug_name not in self.graph:
            return {'direct': [], 'indirect': []}
        
        # Direct neighbors (1-hop)
        direct = list(self.graph.neighbors(drug_name))
        
        # Indirect neighbors (2-hop)
        indirect = set()
        for neighbor in direct:
            indirect.update(self.graph.neighbors(neighbor))
        
        # Remove drug itself and direct neighbors from indirect
        indirect = indirect - set(direct) - {drug_name}
        
        return {
            'direct': direct,
            'indirect': list(indirect)
        }
    
    def get_interaction_path(self, drug_a: str, drug_b: str) -> List[str]:
        """Find shortest path between two drugs"""
        
        if drug_a not in self.graph or drug_b not in self.graph:
            return []
        
        try:
            path = nx.shortest_path(self.graph, drug_a, drug_b)
            return path
        except nx.NetworkXNoPath:
            return []
    
    def get_interaction_severity(self, drug_a: str, drug_b: str) -> Dict:
        """Get severity of interaction between two drugs"""
        
        if not self.graph.has_edge(drug_a, drug_b):
            return {'has_interaction': False}
        
        edge_data = self.graph[drug_a][drug_b]
        
        return {
            'has_interaction': True,
            'severity': edge_data.get('severity', 'unknown'),
            'weight': edge_data.get('weight', 0),
            'description': edge_data.get('description', '')
        }
    
    def find_high_risk_drugs(self, threshold: int = 5) -> List[Tuple[str, int]]:
        """Find drugs with many interactions (potential high risk)"""
        
        degree_dict = dict(self.graph.degree())
        high_risk = [(drug, degree) for drug, degree in degree_dict.items() 
                     if degree >= threshold]
        
        high_risk.sort(key=lambda x: x[1], reverse=True)
        
        return high_risk
    
    def get_drug_clusters(self, num_clusters: int = 5) -> Dict:
        """Find communities of drugs that interact frequently"""
        
        from networkx.algorithms import community
        
        # Find communities
        communities = community.greedy_modularity_communities(self.graph)
        
        clusters = {}
        for i, comm in enumerate(communities[:num_clusters]):
            clusters[f'Cluster_{i+1}'] = list(comm)
        
        return clusters
    
    def compute_drug_centrality(self) -> Dict[str, float]:
        """Compute centrality scores for drugs"""
        
        # Betweenness centrality (drugs that connect many others)
        centrality = nx.betweenness_centrality(self.graph, weight='weight')
        
        # Sort by centrality
        sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        return dict(sorted_centrality[:20])  # Top 20
    
    def save_graph(self, path: str = './data/drug_interaction_graph.json'):
        """Save graph to file"""
        
        # Convert to serializable format
        graph_data = {
            'nodes': list(self.graph.nodes()),
            'edges': [
                {
                    'source': u,
                    'target': v,
                    'weight': data.get('weight', 1),
                    'severity': data.get('severity', 'unknown')
                }
                for u, v, data in self.graph.edges(data=True)
            ],
            'stats': {
                'num_nodes': self.graph.number_of_nodes(),
                'num_edges': self.graph.number_of_edges(),
                'density': nx.density(self.graph)
            }
        }
        
        with open(path, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        logger.info(f"Graph saved to {path}")


class GraphEnhancedRetrieval:
    """Use graph structure to improve retrieval"""
    
    def __init__(self, graph: DrugInteractionGraph, base_retriever):
        self.graph = graph
        self.base_retriever = base_retriever
    
    def retrieve_with_graph_expansion(self, 
                                     query: str, 
                                     query_drugs: List[str],
                                     top_k: int = 5) -> List[Dict]:
        """
        Enhanced retrieval using graph structure:
        1. Standard semantic search
        2. Expand with graph neighbors
        3. Re-rank using both semantic + graph signals
        """
        
        logger.info(f"Graph-enhanced retrieval for: {query_drugs}")
        
        # Stage 1: Standard retrieval
        initial_results = self.base_retriever.search(query, top_k=top_k * 2)
        
        # Stage 2: Graph expansion
        expanded_drugs = set()
        for drug in query_drugs:
            neighbors = self.graph.get_drug_neighbors(drug, max_hops=1)
            expanded_drugs.update(neighbors.get('direct', []))
        
        logger.info(f"Expanded to {len(expanded_drugs)} drugs via graph")
        
        # Stage 3: Re-rank using graph structure
        reranked_results = []
        for doc in initial_results:
            doc_drug = doc.get('drug_name', '')
            interacting_drug = doc.get('interacting_drug', '')
            
            # Calculate graph-based score
            graph_score = 0.0
            
            for query_drug in query_drugs:
                # Check if this document is relevant to query drug
                if doc_drug.lower() in query_drug.lower() or query_drug.lower() in doc_drug.lower():
                    graph_score += 1.0
                
                if interacting_drug:
                    # Check if there's a direct interaction
                    interaction = self.graph.get_interaction_severity(query_drug, interacting_drug)
                    if interaction.get('has_interaction'):
                        graph_score += interaction.get('weight', 1) / 4.0  # Normalize
            
            # Combine semantic and graph scores
            semantic_score = doc.get('relevance_score', 0.0)
            combined_score = 0.6 * semantic_score + 0.4 * graph_score
            
            doc['graph_score'] = graph_score
            doc['combined_score'] = combined_score
            doc['relevance_score'] = combined_score
            
            reranked_results.append(doc)
        
        # Sort by combined score
        reranked_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return reranked_results[:top_k]
    
    def explain_retrieval(self, query_drugs: List[str], retrieved_docs: List[Dict]) -> Dict:
        """Explain why documents were retrieved using graph"""
        
        explanations = []
        
        for doc in retrieved_docs:
            doc_drug = doc.get('drug_name', '')
            interacting_drug = doc.get('interacting_drug', '')
            
            reasons = []
            
            for query_drug in query_drugs:
                # Direct match
                if doc_drug.lower() == query_drug.lower():
                    reasons.append(f"Direct match for {query_drug}")
                
                # Graph connection
                if self.graph.graph.has_edge(query_drug, doc_drug):
                    interaction = self.graph.get_interaction_severity(query_drug, doc_drug)
                    reasons.append(f"Interacts with {query_drug} (severity: {interaction.get('severity')})")
                
                # Path exists
                path = self.graph.get_interaction_path(query_drug, doc_drug)
                if path and len(path) <= 3:
                    reasons.append(f"Connected via: {' -> '.join(path)}")
            
            explanations.append({
                'document': doc_drug,
                'reasons': reasons,
                'score': doc.get('combined_score', 0.0)
            })
        
        return {'explanations': explanations}


# Example usage
if __name__ == '__main__':
    # Test with sample data
    test_chunks = [
        {'drug_name': 'Aspirin', 'description': 'Antiplatelet drug'},
        {'drug_name': 'Warfarin', 'description': 'Anticoagulant'},
        {'drug_name': 'Ibuprofen', 'description': 'NSAID'},
        {
            'drug_name': 'Aspirin',
            'interacting_drug': 'Warfarin',
            'interaction_description': 'Increases risk of serious bleeding. Major interaction.'
        },
        {
            'drug_name': 'Aspirin',
            'interacting_drug': 'Ibuprofen',
            'interaction_description': 'May reduce effectiveness. Moderate interaction.'
        }
    ]
    
    # Build graph
    graph = DrugInteractionGraph()
    graph.build_from_drugbank(test_chunks)
    
    print(f"\nGraph Stats:")
    print(f"  Nodes: {graph.graph.number_of_nodes()}")
    print(f"  Edges: {graph.graph.number_of_edges()}")
    
    # Test neighbor finding
    neighbors = graph.get_drug_neighbors('Aspirin')
    print(f"\nAspirin neighbors:")
    print(f"  Direct: {neighbors['direct']}")
    print(f"  Indirect: {neighbors['indirect']}")
    
    # Test interaction severity
    severity = graph.get_interaction_severity('Aspirin', 'Warfarin')
    print(f"\nAspirin-Warfarin interaction:")
    print(f"  Severity: {severity.get('severity')}")
    print(f"  Weight: {severity.get('weight')}")
