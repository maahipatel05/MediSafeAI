"""
Custom Model Training for Drug Interaction Embeddings
Fine-tunes sentence transformer on DrugBank data
"""

import os
import json
import torch
import random
import logging
from typing import List, Tuple
from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
from torch.utils.data import DataLoader
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DrugInteractionTrainer:
    """Fine-tune embeddings specifically for drug interactions"""
    
    def __init__(self, base_model: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        self.base_model = base_model
        self.model = None
        self.training_examples = []
        
    def prepare_training_data(self, chunks_path: str = './data/chunks_drugbank.json'):
        """
        Create training pairs from DrugBank data
        
        Positive pairs:
        - (Drug A, Drug B) if they interact
        - (Drug name, Drug description)
        - (Drug name, Interaction description)
        
        Negative pairs:
        - (Drug A, Drug C) if they don't interact
        """
        logger.info("Preparing training data from DrugBank...")
        
        with open(chunks_path, 'r') as f:
            chunks = json.load(f)
        
        # Separate main drug chunks from interaction chunks
        drug_chunks = [c for c in chunks if 'interacting_drug' not in c]
        interaction_chunks = [c for c in chunks if 'interacting_drug' in c]
        
        logger.info(f"Found {len(drug_chunks)} drug chunks, {len(interaction_chunks)} interaction chunks")
        
        training_examples = []
        
        # 1. POSITIVE EXAMPLES: Drugs that interact
        logger.info("Creating positive examples from interactions...")
        for int_chunk in interaction_chunks:
            drug_a = int_chunk['drug_name']
            drug_b = int_chunk['interacting_drug']
            interaction_desc = int_chunk['interaction_description']
            
            # Pair 1: Drug names that interact (label=1.0)
            training_examples.append(InputExample(
                texts=[f"Drug: {drug_a}", f"Drug: {drug_b}"],
                label=1.0
            ))
            
            # Pair 2: Drug + interaction description (label=1.0)
            training_examples.append(InputExample(
                texts=[f"Drug: {drug_a}", interaction_desc],
                label=1.0
            ))
            
            # Pair 3: Both drugs + interaction (label=1.0)
            training_examples.append(InputExample(
                texts=[f"Interaction between {drug_a} and {drug_b}", interaction_desc],
                label=1.0
            ))
        
        logger.info(f"Created {len(training_examples)} positive examples")
        
        # 2. NEGATIVE EXAMPLES: Drugs that don't interact
        logger.info("Creating negative examples from non-interactions...")
        
        # Build set of interacting pairs
        interacting_pairs = set()
        for int_chunk in interaction_chunks:
            drug_a = int_chunk['drug_name']
            drug_b = int_chunk['interacting_drug']
            interacting_pairs.add((drug_a, drug_b))
            interacting_pairs.add((drug_b, drug_a))
        
        # Create negative examples
        drug_names = [c['drug_name'] for c in drug_chunks]
        negative_count = 0
        target_negatives = len(training_examples) // 2  # Balance positive/negative
        
        while negative_count < target_negatives:
            drug_a = random.choice(drug_names)
            drug_b = random.choice(drug_names)
            
            if drug_a != drug_b and (drug_a, drug_b) not in interacting_pairs:
                training_examples.append(InputExample(
                    texts=[f"Drug: {drug_a}", f"Drug: {drug_b}"],
                    label=0.0  # No interaction
                ))
                negative_count += 1
        
        logger.info(f"Created {negative_count} negative examples")
        
        # 3. SEMANTIC SIMILARITY: Drug + Description
        logger.info("Creating semantic similarity examples...")
        for drug in drug_chunks[:500]:  # Limit to avoid too many examples
            if drug.get('description'):
                training_examples.append(InputExample(
                    texts=[f"Drug: {drug['drug_name']}", drug['description']],
                    label=0.8  # High similarity but not perfect match
                ))
        
        logger.info(f"Total training examples: {len(training_examples)}")
        
        # Shuffle
        random.shuffle(training_examples)
        self.training_examples = training_examples
        
        return training_examples
    
    def create_evaluation_set(self, num_examples: int = 500) -> evaluation.EmbeddingSimilarityEvaluator:
        """Create held-out evaluation set"""
        
        # Split last N examples for evaluation
        eval_examples = self.training_examples[-num_examples:]
        self.training_examples = self.training_examples[:-num_examples]
        
        sentences1 = [ex.texts[0] for ex in eval_examples]
        sentences2 = [ex.texts[1] for ex in eval_examples]
        scores = [ex.label for ex in eval_examples]
        
        evaluator = evaluation.EmbeddingSimilarityEvaluator(
            sentences1, sentences2, scores,
            name='drugbank_eval'
        )
        
        logger.info(f"Created evaluation set with {num_examples} examples")
        return evaluator
    
    def train(self, 
              output_path: str = './models/drugbank_finetuned',
              epochs: int = 4,
              batch_size: int = 16,
              warmup_steps: int = 100):
        """Fine-tune the model"""
        
        logger.info(f"Loading base model: {self.base_model}")
        self.model = SentenceTransformer(self.base_model)
        
        # Create dataloader
        train_dataloader = DataLoader(
            self.training_examples, 
            shuffle=True, 
            batch_size=batch_size
        )
        
        # Define loss
        train_loss = losses.CosineSimilarityLoss(self.model)
        
        # Create evaluator
        evaluator = self.create_evaluation_set()
        
        # Training
        logger.info(f"Starting training: {epochs} epochs, {len(self.training_examples)} examples")
        
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            evaluator=evaluator,
            epochs=epochs,
            warmup_steps=warmup_steps,
            output_path=output_path,
            evaluation_steps=500,
            save_best_model=True,
            show_progress_bar=True
        )
        
        logger.info(f"Training complete! Model saved to {output_path}")
        return self.model
    
    def evaluate_improvement(self, test_queries: List[Tuple[str, str]]):
        """Compare base model vs fine-tuned model"""
        
        base_model = SentenceTransformer(self.base_model)
        finetuned_model = self.model
        
        results = {
            'base_model': [],
            'finetuned_model': []
        }
        
        for query1, query2 in test_queries:
            # Base model
            base_emb1 = base_model.encode(query1)
            base_emb2 = base_model.encode(query2)
            base_sim = np.dot(base_emb1, base_emb2) / (np.linalg.norm(base_emb1) * np.linalg.norm(base_emb2))
            results['base_model'].append(base_sim)
            
            # Fine-tuned model
            ft_emb1 = finetuned_model.encode(query1)
            ft_emb2 = finetuned_model.encode(query2)
            ft_sim = np.dot(ft_emb1, ft_emb2) / (np.linalg.norm(ft_emb1) * np.linalg.norm(ft_emb2))
            results['finetuned_model'].append(ft_sim)
        
        return results


def main():
    """Main training script"""
    
    # Initialize trainer
    trainer = DrugInteractionTrainer()
    
    # Prepare data
    trainer.prepare_training_data('./data/chunks_drugbank.json')
    
    # Train
    model = trainer.train(
        output_path='./models/drugbank_finetuned',
        epochs=4,
        batch_size=16,
        warmup_steps=100
    )
    
    logger.info("✅ Fine-tuning complete!")
    
    # Test improvement
    test_queries = [
        ("Drug: Aspirin", "Drug: Warfarin"),
        ("Drug: Ibuprofen", "Drug: Aspirin"),
        ("What is aspirin?", "Aspirin is an antiplatelet drug")
    ]
    
    results = trainer.evaluate_improvement(test_queries)
    
    logger.info("Similarity comparison:")
    for i, (q1, q2) in enumerate(test_queries):
        logger.info(f"\nQuery pair {i+1}:")
        logger.info(f"  '{q1}' <-> '{q2}'")
        logger.info(f"  Base model: {results['base_model'][i]:.4f}")
        logger.info(f"  Fine-tuned: {results['finetuned_model'][i]:.4f}")


if __name__ == '__main__':
    main()
