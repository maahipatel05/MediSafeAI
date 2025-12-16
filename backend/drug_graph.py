# drug_graph.py
"""
Simple in-memory knowledge graph for drug-drug interactions.

- Nodes: drug names (strings)
- Edges: interaction between drug_a <-> drug_b
- Edge attributes: severity_code, severity_label, text, doc_id

We load this from a DrugBank-style JSON file, where each record looks like:
{
  "id": "...",
  "drug1": "Aspirin",
  "drug2": "Warfarin",
  "severity": "major",
  "description": "..."
}
"""

import json
from collections import defaultdict
from typing import Dict, Optional


def map_severity_to_code(raw: Optional[str]) -> str:
    """
    Map DrugBank severity labels to S0-S3 codes.

    S3 = high / major
    S2 = moderate
    S1 = minor
    S0 = none / unknown
    """
    if raw is None:
        raw = ""
    raw = raw.strip().lower()

    if raw in ("major", "severe", "contraindicated"):
        return "S3"
    if raw in ("moderate", "significant"):
        return "S2"
    if raw in ("minor", "mild"):
        return "S1"
    return "S0"


class DrugInteractionGraph:
    def __init__(self):
        # adjacency[drug_a][drug_b] = edge_data
        self.adjacency: Dict[str, Dict[str, dict]] = defaultdict(dict)

    @classmethod
    def from_json(cls, path: str) -> "DrugInteractionGraph":
        """
        Build graph from a JSON file of interaction records.

        Adjust the key names here if your JSON schema is different.
        """
        graph = cls()

        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for rec in records:
            drug1 = rec.get("drug1")
            drug2 = rec.get("drug2")
            if not drug1 or not drug2:
                continue

            severity_label = rec.get("severity", "")
            severity_code = map_severity_to_code(severity_label)

            edge_data = {
                "severity_code": severity_code,
                "severity_label": severity_label,
                "doc_id": rec.get("id"),
                "text": rec.get("description") or rec.get("text", ""),
            }

            # Undirected graph: store edge in both directions
            graph.adjacency[drug1][drug2] = edge_data
            graph.adjacency[drug2][drug1] = edge_data

        return graph

    def get_interaction(self, drug_a: str, drug_b: str) -> Optional[dict]:
        """
        Return edge data for (drug_a, drug_b), or None if no interaction.
        """
        return self.adjacency.get(drug_a, {}).get(drug_b)

    def get_neighbors(self, drug: str) -> Dict[str, dict]:
        """
        Return all neighbors and edge data for a given drug.
        """
        return self.adjacency.get(drug, {})