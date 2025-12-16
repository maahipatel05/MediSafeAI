# scripts/drugbank_to_pairwise.py
"""
Convert DrugBank XML (drugbank.xml) into a pairwise interaction file.

For each <drug>:
  <drug>
    <drugbank-id primary="true">DB00001</drugbank-id>
    <name>Lepirudin</name>
    ...
    <drug-interactions>
      <drug-interaction>
        <drugbank-id>DB01323</drugbank-id>
        <name>St. John's Wort</name>
        <description>...</description>
      </drug-interaction>
      ...
    </drug-interactions>
  </drug>

we generate rows like:

  {
    "id": "DB00001-DB01323-1",
    "drug1_id": "DB00001",
    "drug1_name": "Lepirudin",
    "drug2_id": "DB01323",
    "drug2_name": "St. John's Wort",
    "description": "The metabolism of Lepirudin can be increased..."
  }

⚠️ Note: DrugBank’s XML DOES NOT contain a structured severity field for each
interaction; “severity” only appears inside the free-text description.
So here we only output the description and leave severity to be handled later
(e.g., via your ontology / graph logic).
"""

import argparse
import json
import os
import xml.etree.ElementTree as ET
from typing import IO

# DrugBank XML uses a default namespace like "http://www.drugbank.ca"
DB_NS = "{http://www.drugbank.ca}"


def write_jsonl_row(out_f: IO, obj: dict):
    """Write a single JSON object as a line (JSONL format)."""
    out_f.write(json.dumps(obj, ensure_ascii=False))
    out_f.write("\n")


def iter_pairwise_interactions(xml_path: str):
    """
    Stream through drugbank.xml and yield pairwise interaction dicts.

    This uses ET.iterparse so it doesn't load the whole 700MB file into memory.
    """
    context = ET.iterparse(xml_path, events=("end",))
    # We don't care about the root; we process each <drug> as we see it.

    for event, elem in context:
        # We only care when a <drug> element finishes
        if elem.tag != DB_NS + "drug":
            continue

        # 1) primary drug ID and name
        primary_id_elem = elem.find(f"{DB_NS}drugbank-id[@primary='true']")
        name_elem = elem.find(DB_NS + "name")

        if primary_id_elem is None or name_elem is None:
            # If either is missing, skip this drug
            elem.clear()
            continue

        drug1_id = (primary_id_elem.text or "").strip()
        drug1_name = (name_elem.text or "").strip()

        # 2) interactions
        interactions_parent = elem.find(DB_NS + "drug-interactions")
        if interactions_parent is not None:
            index = 0
            for di in interactions_parent.findall(DB_NS + "drug-interaction"):
                d2_id_elem = di.find(DB_NS + "drugbank-id")
                d2_name_elem = di.find(DB_NS + "name")
                desc_elem = di.find(DB_NS + "description")

                if d2_id_elem is None:
                    continue

                index += 1
                drug2_id = (d2_id_elem.text or "").strip()
                drug2_name = (d2_name_elem.text or "").strip() if d2_name_elem is not None else ""
                description = (desc_elem.text or "").strip() if desc_elem is not None else ""

                # Build a unique row ID from the two drug IDs and a counter
                row_id = f"{drug1_id}-{drug2_id}-{index}"

                yield {
                    "id": row_id,
                    "drug1_id": drug1_id,
                    "drug1_name": drug1_name,
                    "drug2_id": drug2_id,
                    "drug2_name": drug2_name,
                    "description": description,
                }

        # Important: free memory for this <drug> subtree
        elem.clear()


def convert_xml_to_jsonl(xml_path: str, out_path: str):
    total_rows = 0
    with open(out_path, "w", encoding="utf-8") as out_f:
        for row in iter_pairwise_interactions(xml_path):
            write_jsonl_row(out_f, row)
            total_rows += 1

    print(f"✅ Done. Wrote {total_rows} interactions to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert DrugBank XML to pairwise interactions (JSONL).")
    parser.add_argument("xml_path", help="Path to drugbank.xml")
    parser.add_argument(
        "out_path",
        nargs="?",
        default="data/drugbank_interactions.jsonl",
        help="Output JSONL file path (default: data/drugbank_interactions.jsonl)",
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out_path), exist_ok=True)
    convert_xml_to_jsonl(args.xml_path, args.out_path)


if __name__ == "__main__":
    main()