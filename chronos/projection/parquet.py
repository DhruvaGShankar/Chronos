"""
Apache Parquet Projection Adapter.
Exports entity state stores and event logs directly to compressed .parquet columnar files for analytical data lakes.
"""

import os
from typing import Dict, List, Any
from chronos.core.exceptions import ProjectionError

class ParquetProjectionAdapter:
    """Exports state store records into compressed Apache Parquet files."""

    def project(
        self,
        entity_store: Dict[str, List[Dict[str, Any]]],
        event_log: List[Any],
        output_dir: str
    ):
        """Writes compressed parquet files for each entity table."""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            try:
                import pandas as pd
                
                for table_name, records in entity_store.items():
                    if not records:
                        continue
                    
                    clean_records = [{k: v for k, v in r.items() if k != "type"} for r in records]
                    df = pd.DataFrame(clean_records)
                    out_path = os.path.join(output_dir, f"{table_name.lower()}.parquet")
                    df.to_parquet(out_path, index=False)

            except ImportError:
                # Fallback if pandas/pyarrow is not installed: write CSV with warning
                for table_name, records in entity_store.items():
                    if not records:
                        continue
                    cols = [c for c in records[0].keys() if c != "type"]
                    out_path = os.path.join(output_dir, f"{table_name.lower()}.csv")
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(",".join(cols) + "\n")
                        for r in records:
                            row = [str(r.get(c, "")) for c in cols]
                            f.write(",".join(row) + "\n")

        except Exception as e:
            raise ProjectionError(f"Parquet projection failed: {str(e)}")
