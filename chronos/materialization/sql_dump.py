"""
SQL Migration Script Exporter.
"""

import os
from typing import Dict, List, Any
from chronos.materialization.base import BaseMaterializer
from chronos.core.types import CausalEvent

class SQLDumpMaterializer(BaseMaterializer):
    """Outputs transactional SQL INSERT scripts ready for execution on relational engines."""

    def materialize(self, entity_store: Dict[str, List[Dict[str, Any]]], event_log: List[CausalEvent], target_path: str = "output/seed.sql"):
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write("-- ==========================================================================\n")
            f.write("-- Chronos Engine v2.0 Enterprise Materialized SQL Dump\n")
            f.write("-- ==========================================================================\n\n")
            f.write("BEGIN;\n\n")

            for table_name, records in entity_store.items():
                if not records:
                    continue

                cols = [k for k in records[0].keys() if k != 'type']
                col_names = ", ".join([f'"{c}"' for c in cols])
                
                f.write(f"-- Table: {table_name}\n")
                f.write(f"INSERT INTO \"{table_name}\" ({col_names}) VALUES\n")

                values_list = []
                for r in records:
                    row_vals = []
                    for c in cols:
                        val = r[c]
                        if isinstance(val, bool):
                            row_vals.append("TRUE" if val else "FALSE")
                        elif isinstance(val, (int, float)):
                            row_vals.append(str(val))
                        else:
                            row_vals.append(f"'{val}'")
                    values_list.append(f"  ({', '.join(row_vals)})")

                f.write(",\n".join(values_list) + ";\n\n")

            f.write("COMMIT;\n")

        print(f"  [SQL Materializer] Exported SQL script to: {target_path}")
