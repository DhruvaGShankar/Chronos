"""
SQLite Database Introspector Implementation.
Introspects live SQLite databases via sqlite3 connection PRAGMA statements.
"""

import sqlite3
from typing import Dict, Any
from chronos.introspection.base import BaseIntrospector
from chronos.introspection.classifier import EntityClassifier
from chronos.introspection.graph import DependencyGraphBuilder
from chronos.core.types import (
    StructuralDomainModel, TableDef, ColumnDef, ColumnType
)
from chronos.core.exceptions import IntrospectionError

class SQLiteIntrospector(BaseIntrospector):
    """Introspects a live SQLite database connection to extract a StructuralDomainModel AST."""

    def inspect(self, db_conn: sqlite3.Connection) -> StructuralDomainModel:
        if not isinstance(db_conn, sqlite3.Connection):
            raise IntrospectionError("Input must be a valid sqlite3.Connection instance.")

        sdm = StructuralDomainModel(domain_name=self.domain_name)
        cursor = db_conn.cursor()

        # 1. Fetch all user tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            raise IntrospectionError("No tables found in the target SQLite database.")

        # 2. Inspect each table schema
        for table_name in tables:
            tdef = TableDef(name=table_name)

            # Columns (PRAGMA table_info)
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            for col in cursor.fetchall():
                # col format: (cid, name, type, notnull, dflt_value, pk)
                c_name = col[1]
                c_type_raw = col[2].upper()
                is_pk = bool(col[5])

                if "INT" in c_type_raw:
                    c_type = ColumnType.INTEGER
                elif any(t in c_type_raw for t in ["FLOAT", "DOUBLE", "NUMERIC", "REAL", "DECIMAL"]):
                    c_type = ColumnType.FLOAT
                elif "BOOL" in c_type_raw:
                    c_type = ColumnType.BOOLEAN
                elif any(t in c_type_raw for t in ["DATE", "TIME"]):
                    c_type = ColumnType.DATETIME
                elif "UUID" in c_type_raw:
                    c_type = ColumnType.UUID
                else:
                    c_type = ColumnType.STRING

                cdef = ColumnDef(
                    name=c_name,
                    data_type=c_type,
                    is_primary_key=is_pk,
                    nullable=not bool(col[3])
                )
                tdef.columns[c_name] = cdef
                if is_pk:
                    tdef.primary_keys.append(c_name)

            # Foreign Keys (PRAGMA foreign_key_list)
            cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
            for fk in cursor.fetchall():
                # fk format: (id, seq, table, from, to, on_update, on_delete, match)
                fk_col = fk[3]
                ref_table = fk[2]
                ref_col = fk[4]

                if fk_col in tdef.columns:
                    tdef.columns[fk_col].is_foreign_key = True
                    tdef.columns[fk_col].fk_ref_table = ref_table
                    tdef.columns[fk_col].fk_ref_column = ref_col

                tdef.foreign_keys.append({fk_col: f"{ref_table}.{ref_col}"})

            sdm.tables[table_name] = tdef

        # 3. Classify Entity Roles and Build Dependency DAG
        for table_name, tdef in sdm.tables.items():
            tdef.inferred_role = EntityClassifier.classify_role(tdef)

        sdm.dependency_dag = DependencyGraphBuilder.build_dependency_dag(sdm.tables)
        return sdm
