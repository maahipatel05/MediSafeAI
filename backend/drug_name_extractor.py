# drug_name_extractor.py
"""
Very simple drug name extractor.

We:
1. Load all unique drug names from the DrugBank interaction JSON.
2. Check which of those names appear in the user query text.
3. Return the first two distinct names as (drug_a, drug_b).

This is naive but works surprisingly well for demo / MVP.
"""

import json
import os
from typing import List, Tuple, Optional

DATA_PATH = os.path.join("data", "drugbank_interactions.json")


def _load_drug_names(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)

    names = set()
    for rec in records:
        d1 = rec.get("drug1")
        d2 = rec.get("drug2")
        if d1:
            names.add(d1.strip())
        if d2:
            names.add(d2.strip())
    return sorted(names)


# Load once at import time
ALL_DRUG_NAMES: List[str] = _load_drug_names(DATA_PATH)


def extract_drug_pair_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to find two drug names from our known list inside the query string.

    Returns:
        (drug_a, drug_b) or (None, None) if we can't find two names.
    """
    q_low = query.lower()
    found: List[str] = []

    for name in ALL_DRUG_NAMES:
        # simple substring check; you can replace with tokenizer-based matching later
        if name.lower() in q_low:
            found.append(name)
        if len(found) == 2:
            break

    if len(found) < 2:
        return None, None

    return found[0], found[1]