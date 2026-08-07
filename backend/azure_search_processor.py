"""
Azure AI Search retrieval backend.

Drop-in match for DrugBankProcessor's public interface (search(query, top_k)
-> List[Dict] with {id, text, source} per result) so nothing downstream
(LocalRetrievalAgent, HybridRetrieval, EnhancedRAGSystem) needs to change to
consume it. Reuses the exact same all-MiniLM-L6-v2 encoder and the exact same
chunks_drugbank.json document set as the FAISS path, so a before/after
retrieval comparison isolates the vector store backend as the only variable.
"""

import os
import json
import base64
import logging
from typing import List, Dict

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from data_processor_drugbank import DrugBankProcessor

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 384
VECTOR_ALGORITHM_NAME = "drugbank-hnsw-algorithm"
VECTOR_PROFILE_NAME = "drugbank-hnsw-profile"
VECTOR_FIELD_NAME = "content_vector"

REQUIRED_ENV_VARS = (
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_API_KEY",
    "AZURE_SEARCH_INDEX_NAME",
)


def require_azure_env() -> Dict[str, str]:
    """Read the Azure AI Search env vars, failing loudly if any are missing.

    RETRIEVAL_BACKEND=azure must never silently fall back to FAISS when
    credentials aren't configured -- that would make it impossible to tell
    whether Azure was actually exercised.
    """
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "RETRIEVAL_BACKEND=azure requires the following environment "
            f"variable(s), which are not set: {', '.join(missing)}. Add them "
            "to backend/.env (see AZURE_RETROFIT_HANDOFF.md Step 0) before "
            "using the Azure backend."
        )
    return {name: os.environ[name] for name in REQUIRED_ENV_VARS}


def safe_document_key(chunk_id: str) -> str:
    """Azure Search document keys allow only letters/digits/_/-/=.

    DrugBank chunk ids (e.g. "Lepirudin_INT_Hydroxyprogesterone caproate")
    contain spaces and other characters pulled straight from drug names, so
    they aren't valid keys as-is. URL-safe base64 encoding produces only
    A-Za-z0-9-_= , which satisfies Azure's key charset, and is reversible if
    ever needed -- though we always carry the original id alongside it in the
    'chunk_id' field so search() can return it unchanged.
    """
    return base64.urlsafe_b64encode(chunk_id.encode("utf-8")).decode("ascii")


def build_index_schema(index_name: str) -> SearchIndex:
    """Azure AI Search index schema matching DrugBankProcessor's chunk shape."""
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="chunk_id", type=SearchFieldDataType.String),
        SearchableField(name="text", type=SearchFieldDataType.String),
        SimpleField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SearchField(
            name=VECTOR_FIELD_NAME,
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name=VECTOR_PROFILE_NAME,
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name=VECTOR_ALGORITHM_NAME)],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE_NAME,
                algorithm_configuration_name=VECTOR_ALGORITHM_NAME,
            )
        ],
    )

    return SearchIndex(name=index_name, fields=fields, vector_search=vector_search)


class AzureSearchProcessor:
    """Azure AI Search-backed retrieval, standing in for DrugBankProcessor."""

    def __init__(self, data_dir: str = "./data"):
        env = require_azure_env()
        self.endpoint = env["AZURE_SEARCH_ENDPOINT"]
        self.api_key = env["AZURE_SEARCH_API_KEY"]
        self.index_name = env["AZURE_SEARCH_INDEX_NAME"]
        self.data_dir = data_dir

        # Reuse DrugBankProcessor's encoder and chunk-loading logic instead of
        # duplicating it, so both backends embed with the identical model and
        # index the identical document set.
        loader = DrugBankProcessor(data_dir=data_dir)
        self.encoder = loader.encoder

        chunks_path = os.path.join(data_dir, "chunks_drugbank.json")
        if os.path.exists(chunks_path):
            logger.info(f"Loading existing chunks from {chunks_path}...")
            with open(chunks_path, "r") as f:
                self.chunks = json.load(f)
        else:
            self.chunks = loader.parse_drugbank_xml()

        credential = AzureKeyCredential(self.api_key)
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=credential,
        )
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint, credential=credential
        )

    def search(self, query: str, top_k: int = 4) -> List[Dict]:
        """Vector-search Azure AI Search, returning the same shape as FAISS."""
        query_vector = self.encoder.encode([query], convert_to_numpy=True)[0].tolist()
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields=VECTOR_FIELD_NAME,
        )

        results = self.search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            top=top_k,
            select=["chunk_id", "text", "source"],
        )

        docs = []
        for r in results:
            docs.append({"id": r["chunk_id"], "text": r["text"], "source": r["source"]})
        return docs
