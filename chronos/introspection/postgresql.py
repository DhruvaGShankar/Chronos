"""
Live PostgreSQL Database Catalog Introspector.
Queries system catalogs (information_schema, pg_catalog, pg_constraint, pg_attribute, pg_description) directly across all user schemas.
"""

from typing import Dict, List, Any
from chronos.core.types import StructuralDomainModel, TableDef, ColumnDef, DataType, EntityRole
from chronos.introspection.base import BaseIntrospector
from chronos.introspection.graph import DependencyGraphBuilder
from chronos.introspection.classifier import EntityClassifier
from chronos.core.exceptions import SchemaIntrospectionError

class PostgreSQLIntrospector(BaseIntrospector):
    """Introspects live PostgreSQL databases querying information_schema and pg_catalog."""

    def inspect(self, db_connection: Any) -> StructuralDomainModel:
        """Introspects PostgreSQL tables, columns, data types, PK/FK constraints across user schemas."""
        try:
            cursor = db_connection.cursor()

            # 1. Query Tables across all non-system schemas
            cursor.execute("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema') 
                  AND table_type = 'BASE TABLE';
            """)
            table_tuples = cursor.fetchall()

            tables: Dict[str, TableDef] = {}

            for tschema, tname in table_tuples:
                full_tname = f"{tschema}.{tname}" if tschema != 'public' else tname

                # 2. Query Columns & Datatypes
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s;
                """, (tschema, tname))
                col_rows = cursor.fetchall()

                columns: Dict[str, ColumnDef] = {}
                primary_keys: List[str] = []
                foreign_keys: List[Dict[str, str]] = []

                for cname, dtype, is_null in col_rows:
                    dt_enum = self._map_pg_type(dtype)
                    columns[cname] = ColumnDef(
                        name=cname,
                        data_type=dt_enum,
                        is_nullable=(is_null == 'YES'),
                        is_primary_key=False,
                        is_foreign_key=False
                    )

                # 3. Query Foreign Keys & Primary Keys via pg_constraint
                cursor.execute("""
                    SELECT
                        tc.constraint_type,
                        kcu.column_name,
                        ccu.table_schema AS foreign_schema,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                    WHERE tc.table_schema = %s AND tc.table_name = %s;
                """, (tschema, tname))

                for ctype, ccol, fschema, ftable, fcol in cursor.fetchall():
                    full_ftable = f"{fschema}.{ftable}" if fschema != 'public' else ftable
                    if ctype == 'PRIMARY KEY':
                        primary_keys.append(ccol)
                        if ccol in columns:
                            columns[ccol].is_primary_key = True
                    elif ctype == 'FOREIGN KEY':
                        fk_dict = {ccol: f"{full_ftable}.{fcol}"}
                        foreign_keys.append(fk_dict)
                        if ccol in columns:
                            columns[ccol].is_foreign_key = True
                            columns[ccol].references = f"{full_ftable}.{fcol}"

                table_def = TableDef(
                    name=full_tname,
                    columns=columns,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys,
                    inferred_role=EntityRole.DIMENSION
                )
                table_def.inferred_role = EntityClassifier.classify_role(table_def)
                tables[full_tname] = table_def

            dag = DependencyGraphBuilder.build_dependency_dag(tables)

            return StructuralDomainModel(
                domain_name=self.domain_name,
                tables=tables,
                dependency_dag=dag
            )

        except Exception as e:
            raise SchemaIntrospectionError(f"PostgreSQL introspection failed: {str(e)}")

    def _map_pg_type(self, pg_type: str) -> DataType:
        pg_type = pg_type.lower()
        if "int" in pg_type or "serial" in pg_type:
            return DataType.INTEGER
        elif "numeric" in pg_type or "decimal" in pg_type or "float" in pg_type or "double" in pg_type or "real" in pg_type:
            return DataType.FLOAT
        elif "bool" in pg_type:
            return DataType.BOOLEAN
        elif "date" in pg_type or "time" in pg_type:
            return DataType.DATETIME
        else:
            return DataType.STRING
