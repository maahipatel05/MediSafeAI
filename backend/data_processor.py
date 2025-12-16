import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import logging
from typing import List, Dict, Tuple
from datasets import load_dataset
import pickle

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize sentence transformer for embeddings
        logger.info("Loading sentence transformer model...")
        self.encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        self.chunks = []
        self.index = None
        
    def load_pubmed_qa_dataset(self) -> List[Dict]:
        """Load and process PubMedQA dataset"""
        logger.info("Loading PubMedQA dataset...")
        try:
            # Load labeled PubMedQA dataset
            dataset = load_dataset("pubmed_qa", "pqa_labeled", split="train")
            
            chunks = []
            for idx, item in enumerate(dataset):
                # Extract question, context, and answer
                question = item.get('question', '')
                context_list = item.get('context', {}).get('contexts', [])
                context = ' '.join(context_list) if context_list else ''
                final_decision = item.get('final_decision', '')
                long_answer = item.get('long_answer', '')
                
                # Create structured chunk
                chunk = {
                    'id': f"pubmed_{idx}",
                    'question': question,
                    'context': context,
                    'answer': final_decision,
                    'explanation': long_answer,
                    'source': 'PubMedQA',
                    'text': f"Question: {question}\n\nContext: {context}\n\nAnswer: {final_decision}\n\nExplanation: {long_answer}"
                }
                chunks.append(chunk)
            
            logger.info(f"Loaded {len(chunks)} chunks from PubMedQA dataset")
            return chunks
        except Exception as e:
            logger.error(f"Error loading PubMedQA dataset: {e}")
            return []
    
    def create_faiss_index(self, chunks: List[Dict]) -> faiss.IndexFlatL2:
        """Create FAISS index from document chunks"""
        logger.info("Creating embeddings and FAISS index...")
        
        # Extract texts for embedding
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.encoder.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype('float32'))
        
        logger.info(f"Created FAISS index with {index.ntotal} vectors")
        return index
    
    def save_index(self, chunks: List[Dict], index: faiss.IndexFlatL2):
        """Save chunks and FAISS index to disk"""
        logger.info("Saving index and chunks...")
        
        # Save chunks as JSON
        chunks_path = os.path.join(self.data_dir, "chunks.json")
        with open(chunks_path, 'w') as f:
            json.dump(chunks, f, indent=2)
        
        # Save FAISS index
        index_path = os.path.join(self.data_dir, "faiss.index")
        faiss.write_index(index, index_path)
        
        logger.info("Index and chunks saved successfully")
    
    def load_index(self) -> Tuple[List[Dict], faiss.IndexFlatL2]:
        """Load chunks and FAISS index from disk"""
        chunks_path = os.path.join(self.data_dir, "chunks.json")
        index_path = os.path.join(self.data_dir, "faiss.index")
        
        if not os.path.exists(chunks_path) or not os.path.exists(index_path):
            logger.info("Index not found, creating new one...")
            chunks = self.load_pubmed_qa_dataset()
            index = self.create_faiss_index(chunks)
            self.save_index(chunks, index)
        else:
            logger.info("Loading existing index...")
            with open(chunks_path, 'r') as f:
                chunks = json.load(f)
            index = faiss.read_index(index_path)
        
        self.chunks = chunks
        self.index = index
        return chunks, index
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for relevant documents using FAISS"""
        if self.index is None or not self.chunks:
            self.load_index()
        
        # Encode query
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Return relevant chunks with scores
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk['relevance_score'] = float(1 / (1 + dist))  # Convert distance to relevance score
                results.append(chunk)
        
        return results

# Initialize global processor
processor = None

def get_processor() -> DataProcessor:
    global processor
    if processor is None:
        processor = DataProcessor()
        processor.load_index()
    return processor
