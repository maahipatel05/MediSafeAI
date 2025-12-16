import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import logging
from typing import List, Dict
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class DrugBankProcessor:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize sentence transformer for embeddings
        # 'all-MiniLM-L6-v2' is perfect for local CPU (fast & small)
        logger.info("Loading sentence transformer model...")
        self.encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        self.chunks = []
        self.index = None
        
    def parse_drugbank_xml(self, xml_file: str = "drugbank.xml") -> List[Dict]:
        """Parse DrugBank XML file and extract drug information"""
        
        # --- FALLBACK FOR MISSING XML ---
        if not os.path.exists(xml_file):
            logger.warning(f"⚠️  {xml_file} not found! Generating MOCK DATA for testing.")
            return self._generate_mock_data()
        # --------------------------------
        
        logger.info(f"Parsing DrugBank XML file: {xml_file}")
        ns = {'db': 'http://www.drugbank.ca'}
        chunks = []
        
        try:
            context = ET.iterparse(xml_file, events=('start', 'end'))
            context = iter(context)
            event, root = next(context)
            
            drug_count = 0
            
            for event, elem in context:
                if event == 'end' and elem.tag == '{http://www.drugbank.ca}drug':
                    drug_count += 1
                    
                    # Extract fields
                    name = elem.findtext('db:name', namespaces=ns, default="Unknown")
                    desc = elem.findtext('db:description', namespaces=ns, default="")
                    mech = elem.findtext('db:mechanism-of-action', namespaces=ns, default="")
                    toxicity = elem.findtext('db:toxicity', namespaces=ns, default="")
                    
                    # 1. GENERAL INFO CHUNK
                    # Keep text under 600 chars for FLAN-T5 context window
                    gen_text = f"Drug: {name}\nDescription: {desc[:300]}..."
                    chunks.append({
                        'id': f"{name}_GEN",
                        'text': gen_text,
                        'source': name
                    })

                    # 2. CLINICAL INFO CHUNK (If mechanism/toxicity exists)
                    if mech or toxicity:
                        clin_text = f"Drug: {name}\nMechanism: {mech[:200]}...\nToxicity: {toxicity[:200]}..."
                        chunks.append({
                            'id': f"{name}_CLIN",
                            'text': clin_text,
                            'source': name
                        })

                    # 3. INTERACTION CHUNKS
                    # Extract interactions
                    interactions_elem = elem.find('db:drug-interactions', namespaces=ns)
                    if interactions_elem is not None:
                        for interaction in interactions_elem.findall('db:drug-interaction', namespaces=ns):
                            target = interaction.findtext('db:name', namespaces=ns, default="")
                            details = interaction.findtext('db:description', namespaces=ns, default="")
                            
                            if target and details:
                                # Highly specific chunk for retrieval
                                int_text = f"Interaction: {name} AND {target}\nDetails: {details}\nRisk: Monitor closely."
                                chunks.append({
                                    'id': f"{name}_INT_{target}",
                                    'text': int_text,
                                    'source': f"{name} + {target}"
                                })

                    elem.clear()
                    root.clear()
                    
                    if drug_count >= 500: # Limit for local demo speed
                        break
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            return self._generate_mock_data()

    def _generate_mock_data(self):
        """Creates dummy data so the system works without the XML file"""
        logger.info("Generating mock drug data...")
        return [
            {"id": "1", "text": "Interaction: Aspirin AND Warfarin\nDetails: May increase risk of bleeding. Monitor INR.", "source": "Mock"},
            {"id": "2", "text": "Interaction: Ibuprofen AND Lisinopril\nDetails: May decrease antihypertensive effect.", "source": "Mock"},
            {"id": "3", "text": "Drug: Aspirin\nDescription: Anti-inflammatory drug used for pain.", "source": "Mock"},
            {"id": "4", "text": "Drug: Warfarin\nDescription: Anticoagulant used to prevent blood clots.", "source": "Mock"},
            {"id": "5", "text": "Interaction: Nitroglycerin AND Sildenafil\nDetails: CONTRAINDICATED. May cause severe hypotension.", "source": "Mock"},
            {"id": "6", "text": "Interaction: Metformin AND Insulin\nDetails: May increase risk of hypoglycemia.", "source": "Mock"}
        ]
    
    def create_faiss_index(self, chunks: List[Dict]):
        """Create FAISS index from chunks"""
        logger.info(f"Creating index for {len(chunks)} chunks...")
        texts = [c['text'] for c in chunks]
        embeddings = self.encoder.encode(texts, convert_to_numpy=True, batch_size=32)
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype('float32'))
        return index
    
    def save_index(self, chunks, index):
        with open(os.path.join(self.data_dir, "chunks_drugbank.json"), 'w') as f:
            json.dump(chunks, f)
        faiss.write_index(index, os.path.join(self.data_dir, "faiss_drugbank.index"))
    
    def load_index(self):
        """Load or create index"""
        chunks_path = os.path.join(self.data_dir, "chunks_drugbank.json")
        index_path = os.path.join(self.data_dir, "faiss_drugbank.index")
        
        if os.path.exists(chunks_path) and os.path.exists(index_path):
            logger.info("Loading existing index...")
            with open(chunks_path, 'r') as f:
                self.chunks = json.load(f)
            self.index = faiss.read_index(index_path)
        else:
            logger.info("Creating new index...")
            self.chunks = self.parse_drugbank_xml()
            self.index = self.create_faiss_index(self.chunks)
            self.save_index(self.chunks, self.index)
            
        return self.chunks, self.index
    
    def search(self, query: str, top_k: int = 4) -> List[Dict]:
        """Search FAISS index"""
        if self.index is None: self.load_index()
        
        # Embed query
        query_vec = self.encoder.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vec.astype('float32'), top_k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.chunks):
                results.append(self.chunks[idx])
        
        return results

# Singleton
processor = None
def get_processor():
    global processor
    if processor is None:
        processor = DrugBankProcessor()
        processor.load_index()
    return processor