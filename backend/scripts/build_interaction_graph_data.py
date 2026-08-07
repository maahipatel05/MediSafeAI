# scripts/build_interaction_graph_data.py
"""
Derive backend/data/drugbank_interactions.json from the already-committed
backend/data/chunks_drugbank.json.

drug_name_extractor.py and drug_graph.DrugInteractionGraph both need a flat
list of {id, drug1, drug2, severity, description} records. That file was
never checked into this repo, so the live LangGraph pipeline can't start.
We don't have the original drugbank.xml (DrugBank requires a license to
redistribute it), but chunks_drugbank.json's interaction chunks already
contain the same real per-pair DrugBank description text -- this script
just reshapes it into the schema drug_graph.py expects, instead of
reparsing anything from scratch.

DrugBank's raw XML has no severity field on <drug-interaction> elements --
only free-text descriptions -- so there's no ground-truth severity label to
extract or to keyword-match against (checked: this corpus has zero
occurrences of "severe"/"fatal"/"contraindicated"/etc.). Rather than fabricate
a keyword rule that would degenerate to one bucket, we reuse the exact
severity classifier this codebase already ships as its ontology fallback
(local_llm_agent.py's ONTOLOGY_CONCEPTS + sentence-embedding similarity),
applied once per real per-pair description text extracted from the chunk.

Usage:
    cd backend && python scripts/build_interaction_graph_data.py
"""

import os
import re
import json

from sentence_transformers import SentenceTransformer, util

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHUNKS_PATH = os.path.join(DATA_DIR, "chunks_drugbank.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "drugbank_interactions.json")

DETAILS_RE = re.compile(r"Details:\s*(.*?)\s*\nRisk:", re.DOTALL)

# Verbatim copy of local_llm_agent.py's ONTOLOGY_CONCEPTS, kept in sync
# deliberately: this is the same S0-S3 rubric the live ontology-fallback
# risk assessor uses, just applied here once at data-build time instead of
# per-query at inference time.
ONTOLOGY_CONCEPTS = [
    {
        "id": "S3_MAJOR",
        "term": (
            "Severe or life-threatening drug interaction that may cause "
            "major bleeding, organ failure, or death. The combination is often "
            "contraindicated."
        ),
        "severity": "S3",
    },
    {
        "id": "S2_MODERATE",
        "term": (
            "Clinically significant interaction that usually requires dose "
            "adjustment, therapy modification, or close monitoring."
        ),
        "severity": "S2",
    },
    {
        "id": "S1_MINOR",
        "term": (
            "Minor interaction with limited clinical impact. It may cause mild "
            "side effects but usually does not require a change in therapy."
        ),
        "severity": "S1",
    },
    {
        "id": "S0_NONE",
        "term": (
            "No clinically meaningful drug interaction is known. The "
            "combination is generally considered safe."
        ),
        "severity": "S0",
    },
]

MIN_CONFIDENCE = 0.40
CODE_TO_LABEL = {"S3": "major", "S2": "moderate", "S1": "minor", "S0": ""}


def main():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    parsed = []
    for chunk in chunks:
        if "_INT_" not in chunk["id"]:
            continue
        source = chunk.get("source", "")
        if " + " not in source:
            continue
        drug1, drug2 = (s.strip() for s in source.split(" + ", 1))
        if not drug1 or not drug2:
            continue
        match = DETAILS_RE.search(chunk.get("text", ""))
        details = match.group(1).strip() if match else ""
        parsed.append({"id": chunk["id"], "drug1": drug1, "drug2": drug2, "description": details})

    print(f"Loading sentence transformer model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    ontology_texts = [c["term"] for c in ONTOLOGY_CONCEPTS]
    ontology_embeddings = model.encode(ontology_texts, convert_to_tensor=True)

    print(f"Classifying severity for {len(parsed)} interaction descriptions...")
    desc_texts = [p["description"] or p["drug1"] + " " + p["drug2"] for p in parsed]
    desc_embeddings = model.encode(desc_texts, convert_to_tensor=True, batch_size=64, show_progress_bar=True)

    sims = util.cos_sim(desc_embeddings, ontology_embeddings)

    records = []
    severities = {}
    for i, p in enumerate(parsed):
        scores = sims[i]
        top_idx = int(scores.argmax())
        top_score = float(scores[top_idx])
        severity_code = ONTOLOGY_CONCEPTS[top_idx]["severity"]
        if top_score < MIN_CONFIDENCE:
            severity_code = "S0"
        label = CODE_TO_LABEL[severity_code]
        severities[label or "unknown"] = severities.get(label or "unknown", 0) + 1
        records.append(
            {
                "id": p["id"],
                "drug1": p["drug1"],
                "drug2": p["drug2"],
                "severity": label,
                "description": p["description"],
            }
        )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"records written: {len(records)}")
    print(f"severity breakdown: {severities}")
    print(f"output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
