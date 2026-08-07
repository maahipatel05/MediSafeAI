# scripts/upload_to_azure_search.py
"""
One-time index population script for the Azure AI Search retrieval backend.

Loads the *existing* backend/data/chunks_drugbank.json (already built by the
FAISS path -- this script does not reparse drugbank.xml or regenerate
chunks), creates the Azure AI Search index if it doesn't exist, embeds every
chunk with the same all-MiniLM-L6-v2 encoder used by DrugBankProcessor, and
batch-uploads the documents. This guarantees both backends index the
identical document set, which is required for a fair before/after
retrieval comparison.

Usage:
    cd backend && python scripts/upload_to_azure_search.py
"""

import os
import sys
import json
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

from azure_search_processor import (
    build_index_schema,
    require_azure_env,
    safe_document_key,
    VECTOR_FIELD_NAME,
)
from data_processor_drugbank import DrugBankProcessor

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def ensure_index(index_client: SearchIndexClient, index_name: str) -> None:
    try:
        index_client.get_index(index_name)
        logger.info(f"Index '{index_name}' already exists, reusing it.")
    except ResourceNotFoundError:
        logger.info(f"Index '{index_name}' not found, creating it...")
        index_client.create_index(build_index_schema(index_name))
        logger.info(f"Index '{index_name}' created.")


def load_chunks(data_dir: str):
    chunks_path = os.path.join(data_dir, "chunks_drugbank.json")
    if not os.path.exists(chunks_path):
        raise FileNotFoundError(
            f"{chunks_path} not found. Run the FAISS build first "
            "(data_processor_drugbank.get_processor()) so both backends "
            "index the same chunks -- this script does not regenerate them."
        )
    with open(chunks_path, "r") as f:
        return json.load(f)


def main():
    env = require_azure_env()
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    chunks = load_chunks(data_dir)
    logger.info(f"Loaded {len(chunks)} chunks from chunks_drugbank.json")

    logger.info("Loading sentence transformer model (all-MiniLM-L6-v2)...")
    encoder = DrugBankProcessor(data_dir=data_dir).encoder

    credential = AzureKeyCredential(env["AZURE_SEARCH_API_KEY"])
    index_client = SearchIndexClient(endpoint=env["AZURE_SEARCH_ENDPOINT"], credential=credential)
    search_client = SearchClient(
        endpoint=env["AZURE_SEARCH_ENDPOINT"],
        index_name=env["AZURE_SEARCH_INDEX_NAME"],
        credential=credential,
    )

    ensure_index(index_client, env["AZURE_SEARCH_INDEX_NAME"])

    logger.info(f"Encoding {len(chunks)} chunk texts...")
    texts = [c["text"] for c in chunks]
    embeddings = encoder.encode(texts, convert_to_numpy=True, batch_size=32, show_progress_bar=True)

    documents = []
    for chunk, vector in zip(chunks, embeddings):
        documents.append(
            {
                "id": safe_document_key(chunk["id"]),
                "chunk_id": chunk["id"],
                "text": chunk["text"],
                "source": chunk["source"],
                VECTOR_FIELD_NAME: vector.tolist(),
            }
        )

    total_uploaded = 0
    num_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        # Free tier throttles aggressively under bulk indexing -- observed as
        # both HTTP 429 and HTTP 503 ("too many requests"). Retry both with
        # exponential backoff rather than failing the whole run.
        result = None
        max_retries = 10
        for attempt in range(max_retries):
            try:
                result = search_client.upload_documents(documents=batch)
                break
            except HttpResponseError as e:
                if e.status_code in (429, 503) and attempt < max_retries - 1:
                    wait_s = min(2 ** attempt, 60)
                    logger.warning(
                        f"Batch {batch_num}/{num_batches} throttled "
                        f"({e.status_code}), retrying in {wait_s}s "
                        f"(attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(wait_s)
                else:
                    raise
        # Small pacing delay between batches to avoid immediately re-triggering
        # Free tier throttling on the next request.
        time.sleep(1)

        succeeded = sum(1 for r in result if r.succeeded)
        total_uploaded += succeeded
        logger.info(
            f"Uploaded batch {batch_num}/{num_batches} "
            f"({succeeded}/{len(batch)} succeeded)"
        )
        if succeeded < len(batch):
            for r in result:
                if not r.succeeded:
                    logger.error(f"  Failed doc key={r.key}: {r.error_message}")

    print(f"documents indexed: {total_uploaded}")


if __name__ == "__main__":
    main()
