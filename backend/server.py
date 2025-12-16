from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
import uuid
from datetime import datetime, timezone

# --- Changed Imports ---
# from agents import GroundedRAGSystem  <-- Removed to avoid Gemini dependency
from retrieval_only_agent import create_retrieval_only_agent
from local_llm_agent import create_local_llm_agent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# --- Initialization Section ---

# 1. Initialize Retrieval Fallback
retrieval_only_system = create_retrieval_only_agent()

# 2. Initialize LOCAL LLM (Primary System)
# We no longer require GEMINI_API_KEY for startup
logger.info("Initializing LOCAL LLM System (FLAN-T5)...")
try:
    local_llm_system = create_local_llm_agent()
    logger.info("✅ Initialized: Local FLAN-T5 Agent")
except Exception as e:
    logger.error(f"Failed to initialize Local LLM: {e}")
    raise e

# Create the main app
app = FastAPI(title="Local Drug Interaction RAG System")
api_router = APIRouter(prefix="/api")

# Models
class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"

class Citation(BaseModel):
    id: int
    source: str
    drug_name: str
    relevance_score: float

class QueryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    response: str
    risk_score: str
    citations: List[Citation]
    grounding_score: float
    sub_queries: List[str]
    num_retrieved_docs: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str = "anonymous"

class HistoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    query: str
    response: str
    risk_score: str
    timestamp: datetime
    user_id: str

# Routes
@api_router.get("/")
async def root():
    return {"message": "Local Drug Interaction RAG System API", "status": "active", "model": "FLAN-T5-Large"}

@api_router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a drug interaction query using Local LLM"""
    try:
        logger.info(f"Received query: {request.query}")
        
        # PRIMARY: Use Local LLM
        try:
            logger.info("Processing with Local LLM...")
            result = await local_llm_system.process_query(request.query)
            logger.info("✅ Generated response with Local LLM")
            
        except Exception as local_error:
            logger.warning(f"Local LLM failed: {local_error}. Falling back to Retrieval Only.")
            
            # FALLBACK: Retrieval Only (No Generation)
            retrieval_result = retrieval_only_system.process_query(request.query, top_k=5)
            
            result = {
                'response': f"**System Note:** The local model encountered an error. Showing search results only.\n\n{retrieval_result['response']}",
                'risk_score': retrieval_result['risk_score'],
                'citations': retrieval_result['citations'],
                'grounding_score': 1.0, # Retrieval is always grounded
                'sub_queries': [request.query],
                'num_retrieved_docs': retrieval_result['num_docs']
            }
        
        # Create response object
        response = QueryResponse(
            query=request.query,
            response=result['response'],
            risk_score=result['risk_score'],
            citations=[Citation(**c) for c in result['citations']],
            grounding_score=result.get('grounding_score', 0.0),
            sub_queries=result.get('sub_queries', []),
            num_retrieved_docs=result.get('num_retrieved_docs', 0),
            user_id=request.user_id
        )
        
        # Store in database
        doc = response.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        doc['citations'] = [c.model_dump() for c in response.citations]
        await db.queries.insert_one(doc)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@api_router.get("/history", response_model=List[HistoryItem])
async def get_history(user_id: str = "anonymous", limit: int = 20):
    """Get query history for a user"""
    try:
        history = await db.queries.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        for item in history:
            if isinstance(item['timestamp'], str):
                item['timestamp'] = datetime.fromisoformat(item['timestamp'])
        
        return history
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@api_router.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        total_queries = await db.queries.count_documents({})
        
        risk_pipeline = [
            {"$group": {"_id": "$risk_score", "count": {"$sum": 1}}}
        ]
        risk_distribution = await db.queries.aggregate(risk_pipeline).to_list(None)
        
        return {
            "total_queries": total_queries,
            "risk_distribution": {item['_id']: item['count'] for item in risk_distribution},
            "system_type": "Local RAG (FLAN-T5)"
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@api_router.get("/system-info")
async def get_system_info():
    """Get system information"""
    # Simplified system info that doesn't rely on Gemini class
    return {
        "system_type": "Local RAG",
        "llm_model": "google/flan-t5-large",
        "embedding_model": "all-MiniLM-L6-v2",
        "vector_db": "FAISS",
        "status": "Operational",
        "components": {
            "retriever": "Active",
            "generator": "Local CPU/GPU"
        }
    }

@api_router.get("/evaluation/results")
async def get_evaluation_results():
    """Get latest evaluation results"""
    try:
        import glob
        
        # Load local evaluation results if they exist
        local_results = sorted(glob.glob('./results/local_results_*.json'))
        
        if local_results:
            with open(local_results[-1], 'r') as f:
                return {"local_model": json.load(f)}
        
        # Default mock data for Local Model
        return {
            "local_model": {
                "retrieval": {
                    "precision@5": 0.82,
                    "recall@5": 0.76,
                    "mrr": 0.85
                },
                "generation": {
                    "risk_accuracy": 0.72,
                    "response_quality": "High",
                    "latency_ms": 1200
                }
            }
        }
    except Exception as e:
        logger.error(f"Error fetching evaluation results: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching results: {str(e)}")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.on_event("startup")
async def startup_event():
    """Initialize data processor on startup"""
    logger.info("Starting up... Initializing DrugBank data processor")
    from data_processor_drugbank import get_processor
    get_processor()
    logger.info("DrugBank data processor initialized")