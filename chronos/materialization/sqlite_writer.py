"""
SQLite Direct Database Materializer.
Materializes simulated organizational state directly into a live SQLite database.
"""

import sqlite3
from typing import Dict, List, Any
from chronos.materialization.base import BaseMaterializer
from chronos.core.types import CausalEvent

class SQLiteMaterializer(BaseMaterializer):
    """Inserts simulated entity states directly into an active sqlite3 connection."""

    def materialize(self, entity_store: Dict[str, List[Dict[str, Any]]], event_log: List[CausalEvent], db_conn: sqlite3.Connection):
        cursor = db_conn.cursor()

        for table_name, records in entity_store.items():
            if not records:
                continue

            # Filter fields that exist in the target table schema
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            db_cols = [col[1] for col in cursor.fetchall()]

            if not db_cols:
                continue

            cols_str = ", ".join([f'"{c}"' for c in db_cols])
            placeholders = ", ".join(["?"] * len(db_cols))
            insert_sql = f"INSERT INTO \"{table_name}\" ({cols_str}) VALUES ({placeholders});"

            rows_to_insert = []
            for r in records:
                row_vals = []
                for col in db_cols:
                    val = r.get(col, None)
                    if isinstance(val, bool):
                        val = 1 if val else 0
                    row_vals.append(val)
                rows_to_insert.append(tuple(row_vals))

            cursor.executemany(insert_sql, rows_to_insert)

        db_conn.commit()
        print(f"  [SQLite Materializer] Directly populated simulated records into database tables.")
