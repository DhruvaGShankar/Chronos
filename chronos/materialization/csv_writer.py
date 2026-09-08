"""
CSV File Exporter.
"""

import os
import csv
from typing import Dict, List, Any
from chronos.materialization.base import BaseMaterializer
from chronos.core.types import CausalEvent

class CSVMaterializer(BaseMaterializer):
    """Exports materialized entity states as normalized CSV table files."""

    def materialize(self, entity_store: Dict[str, List[Dict[str, Any]]], event_log: List[CausalEvent], target_path: str = "output/csv/"):
        os.makedirs(target_path, exist_ok=True)

        for table_name, records in entity_store.items():
            if not records:
                continue

            cols = [k for k in records[0].keys() if k != 'type']
            filepath = os.path.join(target_path, f"{table_name.lower()}.csv")

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
                for r in records:
                    writer.writerow({c: r[c] for c in cols})

        print(f"  [CSV Materializer] Exported CSV tables to directory: {target_path}")
