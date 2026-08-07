"""
LangGraph-orchestrated drug interaction RAG pipeline.

Replaces the linear process_query() loop in LocalLLMAgent with a
stateful StateGraph. Each processing step is an explicit node; the
risk assessment uses a conditional edge to route between graph-based
severity (preferred) and ontology-based fallback — making the
decision point visible and testable.

Graph topology:
    expand → retrieve → generate → graph_risk ──(found)──→ compile → END
                                              └─(missing)─→ ontology_risk → compile
"""
import logging
import asyncio
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, START, END

logger = logging.getLogger(__name__)


class DrugQueryState(TypedDict):
    """Shared state threaded through every node in the pipeline."""
    query: str
    drug_a: Optional[str]
    drug_b: Optional[str]
    expanded_query: str
    retrieved_docs: List[Dict[str, Any]]
    context_text: str
    generated_text: str
    risk_score: Optional[str]
    response: str
    citations: List[Dict[str, Any]]
    grounding_score: float
    confidence_info: Dict[str, Any]
    sub_queries: List[str]
    num_retrieved_docs: int


def build_drug_rag_graph(agent):
    """
    Compile a LangGraph StateGraph for the drug RAG pipeline.
    `agent` is a LocalLLMAgent — we reuse its already-loaded models.
    """

    def expand_node(state: DrugQueryState) -> DrugQueryState:
        """Node 1: Agent 1 (QueryAgent) - drug-pair extraction + query expansion."""
        decomposed = agent.query_agent.decompose(state["query"])
        return {**state, **decomposed}

    def retrieve_node(state: DrugQueryState) -> DrugQueryState:
        """Node 2: Agent 2 (RetrievalAgent) - bi-encoder top-20 -> cross-encoder top-5."""
        docs, context = agent.retrieval_agent.retrieve(state["expanded_query"])
        return {
            **state,
            "retrieved_docs": docs,
            "context_text": context,
            "num_retrieved_docs": len(docs),
        }

    def generate_node(state: DrugQueryState) -> DrugQueryState:
        """Node 3: Agent 3 (GenerationAgent) - FLAN-T5 generation over retrieved context."""
        generated = agent.generation_agent.generate(state["query"], state["context_text"])
        logger.info(f"[generate] {len(generated)} chars produced")
        return {**state, "generated_text": generated}

    def graph_risk_node(state: DrugQueryState) -> DrugQueryState:
        """Node 4a: Agent 3 - graph-based severity look-up (preferred path)."""
        risk = None
        if state["drug_a"] and state["drug_b"]:
            risk = agent.generation_agent._assess_risk_graph(state["drug_a"], state["drug_b"])
            logger.info(f"[graph_risk] {state['drug_a']} + {state['drug_b']} → {risk}")
        return {**state, "risk_score": risk}

    def ontology_risk_node(state: DrugQueryState) -> DrugQueryState:
        """Node 4b: Agent 3 - ontology fallback when no graph edge exists."""
        risk = agent.generation_agent._assess_risk_ontology(
            state["retrieved_docs"], state["generated_text"]
        )
        logger.info(f"[ontology_risk] fallback → {risk}")
        return {**state, "risk_score": risk}

    def compile_node(state: DrugQueryState) -> DrugQueryState:
        """Node 5: Agent 3 - response formatting, citations, grounding + confidence."""
        result = agent.generation_agent.finalize(
            state["query"], state["generated_text"], state["retrieved_docs"]
        )
        return {
            **state,
            "response": result["response"],
            "citations": result["citations"],
            "grounding_score": result["grounding_score"],
            "confidence_info": result["confidence_info"],
        }

    def route_risk(state: DrugQueryState) -> str:
        """Conditional edge: skip ontology if the knowledge graph already answered."""
        return "compile" if state["risk_score"] is not None else "ontology_risk"

    graph = StateGraph(DrugQueryState)

    graph.add_node("expand", expand_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("graph_risk", graph_risk_node)
    graph.add_node("ontology_risk", ontology_risk_node)
    graph.add_node("compile", compile_node)

    graph.add_edge(START, "expand")
    graph.add_edge("expand", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "graph_risk")
    graph.add_conditional_edges(
        "graph_risk",
        route_risk,
        {"compile": "compile", "ontology_risk": "ontology_risk"},
    )
    graph.add_edge("ontology_risk", "compile")
    graph.add_edge("compile", END)

    compiled = graph.compile()
    logger.info("✅ LangGraph drug RAG pipeline compiled (5 nodes, 1 conditional edge)")
    return compiled


class LangGraphDrugAgent:
    """
    Drop-in async replacement for LocalLLMAgent.process_query(),
    orchestrated via a compiled LangGraph StateGraph.
    """

    def __init__(self, base_agent):
        self._base = base_agent
        self._graph = build_drug_rag_graph(base_agent)

    async def process_query(self, query: str) -> Dict[str, Any]:
        initial: DrugQueryState = {
            "query": query,
            "drug_a": None,
            "drug_b": None,
            "expanded_query": "",
            "retrieved_docs": [],
            "context_text": "",
            "generated_text": "",
            "risk_score": None,
            "response": "",
            "citations": [],
            "grounding_score": 0.0,
            "confidence_info": {},
            "sub_queries": [],
            "num_retrieved_docs": 0,
        }
        loop = asyncio.get_event_loop()
        final = await loop.run_in_executor(None, self._graph.invoke, initial)
        return {
            "query": final["query"],
            "response": final["response"],
            "risk_score": final["risk_score"],
            "citations": final["citations"],
            "grounding_score": final["grounding_score"],
            "confidence_info": final["confidence_info"],
            "sub_queries": final["sub_queries"],
            "num_retrieved_docs": final["num_retrieved_docs"],
        }
