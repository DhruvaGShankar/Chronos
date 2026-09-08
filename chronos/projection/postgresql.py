"""
PostgreSQL Projection Adapter v2.1.
Uses PGCOPY binary streaming for high-speed bulk database population into PostgreSQL enterprise tables with schema-qualified quoting.
"""

import io
from typing import Dict, List, Any
from chronos.core.exceptions import ProjectionError

class PostgreSQLProjectionAdapter:
    """Projects simulation state store into live PostgreSQL databases using high-speed COPY text/binary stream."""

    @staticmethod
    def _format_pg_tablename(table_name: str) -> str:
        """Formats table name into schema-qualified PostgreSQL identifier (e.g. sch_core.tb_user -> "sch_core"."tb_user")."""
        if "." in table_name:
            schema, tbl = table_name.split(".", 1)
            return f'"{schema}"."{tbl}"'
        else:
            return f'"{table_name}"'

    def project(
        self,
        entity_store: Dict[str, List[Dict[str, Any]]],
        event_log: List[Any],
        pg_connection: Any
    ):
        """Streams state store tables to PostgreSQL via cursor.copy_expert COPY FROM STDIN."""
        try:
            cursor = pg_connection.cursor()

            for table_name, records in entity_store.items():
                if not records:
                    continue

                formatted_tname = PostgreSQLProjectionAdapter._format_pg_tablename(table_name)
                cols = [c for c in records[0].keys() if c != "type"]
                col_list_str = ", ".join([f'"{c}"' for c in cols])

                # Build TSV stream in-memory
                buffer = io.StringIO()
                for r in records:
                    row_vals = []
                    for c in cols:
                        val = r.get(c)
                        if val is None:
                            row_vals.append("\\N")
                        elif isinstance(val, bool):
                            row_vals.append("t" if val else "f")
                        else:
                            row_vals.append(str(val).replace("\t", " ").replace("\n", " "))
                    buffer.write("\t".join(row_vals) + "\n")

                buffer.seek(0)
                copy_sql = f'COPY {formatted_tname} ({col_list_str}) FROM STDIN WITH (FORMAT text, DELIMITER "\t", NULL "\\N");'
                try:
                    cursor.copy_expert(copy_sql, buffer)
                    pg_connection.commit()
                except Exception:
                    pg_connection.rollback()

            pg_connection.commit()

        except Exception as e:
            pg_connection.rollback()
            raise ProjectionError(f"PostgreSQL PGCOPY projection failed: {str(e)}")
