"""
SQL DDL Introspector Implementation.
Parses raw SQL migration DDL strings into a StructuralDomainModel AST.
"""

import re
from typing import Dict, Any
from chronos.introspection.base import BaseIntrospector
from chronos.introspection.classifier import EntityClassifier
from chronos.introspection.graph import DependencyGraphBuilder
from chronos.core.types import (
    StructuralDomainModel, TableDef, ColumnDef, ColumnType
)
from chronos.core.exceptions import IntrospectionError

class SQLDDLIntrospector(BaseIntrospector):
    """Parses ANSI SQL DDL statements into a StructuralDomainModel AST."""

    def inspect(self, sql_ddl: str) -> StructuralDomainModel:
        if not isinstance(sql_ddl, str) or not sql_ddl.strip():
            raise IntrospectionError("SQL DDL input must be a non-empty string.")

        sdm = StructuralDomainModel(domain_name=self.domain_name)

        # 1. Clean SQL comments
        clean_sql = re.sub(r'--.*?\n', '', sql_ddl)
        clean_sql = re.sub(r'/\*.*?\*/', '', clean_sql, flags=re.DOTALL)

        # 2. Extract CREATE TABLE blocks
        create_table_blocks = re.findall(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?\s*\((.*?)\);',
            clean_sql, re.IGNORECASE | re.DOTALL
        )

        if not create_table_blocks:
            raise IntrospectionError("No valid 'CREATE TABLE' statements found in SQL DDL.")

        for table_name, body in create_table_blocks:
            tdef = TableDef(name=table_name)
            lines = [line.strip() for line in body.split(',') if line.strip()]

            for line in lines:
                # Primary Key Constraint
                if line.upper().startswith("PRIMARY KEY"):
                    pk_match = re.search(r'PRIMARY\s+KEY\s*\(["`]?(\w+)["`]?\)', line, re.IGNORECASE)
                    if pk_match:
                        pk_col = pk_match.group(1)
                        if pk_col in tdef.columns:
                            tdef.columns[pk_col].is_primary_key = True
                        if pk_col not in tdef.primary_keys:
                            tdef.primary_keys.append(pk_col)
                    continue

                # Foreign Key Constraint
                if line.upper().startswith("FOREIGN KEY") or "REFERENCES" in line.upper():
                    fk_match = re.search(
                        r'FOREIGN\s+KEY\s*\(["`]?(\w+)["`]?\)\s+REFERENCES\s+["`]?(\w+)["`]?\s*\(["`]?(\w+)["`]?\)',
                        line, re.IGNORECASE
                    )
                    if fk_match:
                        fk_col, ref_table, ref_col = fk_match.groups()
                        if fk_col in tdef.columns:
                            tdef.columns[fk_col].is_foreign_key = True
                            tdef.columns[fk_col].fk_ref_table = ref_table
                            tdef.columns[fk_col].fk_ref_column = ref_col
                        tdef.foreign_keys.append({fk_col: f"{ref_table}.{ref_col}"})
                    continue

                # Standard Column Definition
                col_parts = line.split()
                if not col_parts:
                    continue
                
                col_name = col_parts[0].strip('"`[]')
                col_type_raw = col_parts[1].upper() if len(col_parts) > 1 else "VARCHAR"

                # DataType Mapping
                if "INT" in col_type_raw:
                    c_type = ColumnType.INTEGER
                elif any(t in col_type_raw for t in ["FLOAT", "DOUBLE", "NUMERIC", "DECIMAL"]):
                    c_type = ColumnType.FLOAT
                elif "BOOL" in col_type_raw:
                    c_type = ColumnType.BOOLEAN
                elif any(t in col_type_raw for t in ["DATE", "TIME", "TIMESTAMP"]):
                    c_type = ColumnType.DATETIME
                elif "UUID" in col_type_raw:
                    c_type = ColumnType.UUID
                else:
                    c_type = ColumnType.STRING

                is_pk = "PRIMARY KEY" in line.upper()
                cdef = ColumnDef(
                    name=col_name,
                    data_type=c_type,
                    is_primary_key=is_pk,
                    is_nullable="NOT NULL" not in line.upper()
                )

                tdef.columns[col_name] = cdef
                if is_pk:
                    tdef.primary_keys.append(col_name)

            sdm.tables[table_name] = tdef

        # 3. Classify Roles and Construct Dependency DAG
        for table_name, tdef in sdm.tables.items():
            tdef.inferred_role = EntityClassifier.classify_role(tdef)

        sdm.dependency_dag = DependencyGraphBuilder.build_dependency_dag(sdm.tables)

        return sdm
