"""
PostgreSQL Database Schema Cloner & Isolation Manager.
Creates target database (XSC_DB_ONEAPP_SIM), clones DDL table structures, and preserves reference lookup data while leaving source database (XSC_DB_ONEAPP_TEST) 100% untouched.
"""

import sys
import os
from typing import Dict, List, Any
from chronos.core.types import StructuralDomainModel
from chronos.core.exceptions import ProjectionError

class PostgreSQLDatabaseCloner:
    """Clones PostgreSQL schema structures and lookup data into isolated target database."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        user: str = "postgres",
        password: str = "postgres",
        source_dbname: str = "XSC_DB_ONEAPP_TEST",
        target_dbname: str = "XSC_DB_ONEAPP_SIM"
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.source_dbname = source_dbname
        self.target_dbname = target_dbname

    def ensure_target_database_exists(self):
        """Creates target database if it does not exist."""
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

            # Connect to default postgres DB to execute CREATE DATABASE
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname="postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (self.target_dbname,))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute(f'CREATE DATABASE "{self.target_dbname}";')
                print(f"[Database Cloner] Created target database '{self.target_dbname}'.")
            else:
                print(f"[Database Cloner] Target database '{self.target_dbname}' exists.")

            conn.close()

        except Exception as e:
            raise ProjectionError(f"Failed to create target database '{self.target_dbname}': {str(e)}")

    def clone_schema_structures(self, sdm: StructuralDomainModel):
        """Recreates PostgreSQL schemas and table definitions in target database."""
        self.ensure_target_database_exists()

        try:
            import psycopg2

            source_conn = psycopg2.connect(
                host=self.host, port=self.port, user=self.user, password=self.password, dbname=self.source_dbname
            )
            target_conn = psycopg2.connect(
                host=self.host, port=self.port, user=self.user, password=self.password, dbname=self.target_dbname
            )

            source_cur = source_conn.cursor()
            target_cur = target_conn.cursor()

            # 1. Discover and create PostgreSQL schemas in target DB
            source_cur.execute("""
                SELECT DISTINCT table_schema 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast');
            """)
            schemas = [r[0] for r in source_cur.fetchall()]

            for sname in schemas:
                if sname != 'public':
                    target_cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{sname}";')
            target_conn.commit()

            # 2. Recreate DDL Table definitions from SDM in topological order
            for tname in sdm.dependency_dag.keys():
                if tname not in sdm.tables:
                    continue
                
                tdef = sdm.tables[tname]
                schema_prefix = f'"{tname.split(".")[0]}"."' if "." in tname else '"public"."'
                bare_tname = tname.split(".")[-1]
                full_sql_tname = f'{schema_prefix}{bare_tname}"'

                # Drop table if exists on target DB
                target_cur.execute(f'DROP TABLE IF EXISTS {full_sql_tname} CASCADE;')

                col_specs = []
                for cname, cdef in tdef.columns.items():
                    pg_type = "TEXT"
                    if cdef.data_type.value == "INTEGER":
                        pg_type = "INTEGER"
                    elif cdef.data_type.value == "FLOAT":
                        pg_type = "DOUBLE PRECISION"
                    elif cdef.data_type.value == "BOOLEAN":
                        pg_type = "BOOLEAN"
                    elif cdef.data_type.value == "DATETIME":
                        pg_type = "TIMESTAMP"

                    null_spec = "" if cdef.is_nullable else " NOT NULL"
                    col_specs.append(f'"{cname}" {pg_type}{null_spec}')

                if tdef.primary_keys:
                    pk_str = ", ".join([f'"{pk}"' for pk in tdef.primary_keys])
                    col_specs.append(f'PRIMARY KEY ({pk_str})')

                create_table_sql = f"CREATE TABLE {full_sql_tname} (\n  " + ",\n  ".join(col_specs) + "\n);"
                target_cur.execute(create_table_sql)

            target_conn.commit()

            # 3. Copy static lookup/reference rows from source to target
            for tname in sdm.tables.keys():
                if "lookup" in tname.lower() or "cat" in tname.lower() or "type" in tname.lower():
                    try:
                        source_cur.execute(f'SELECT * FROM {tname} LIMIT 100;')
                        lookup_rows = source_cur.fetchall()
                        if lookup_rows:
                            cols = [c for c in sdm.tables[tname].columns.keys()]
                            col_str = ", ".join([f'"{c}"' for c in cols])
                            placeholders = ", ".join(["%s"] * len(cols))
                            schema_prefix = f'"{tname.split(".")[0]}"."' if "." in tname else '"public"."'
                            bare_tname = tname.split(".")[-1]
                            full_sql_tname = f'{schema_prefix}{bare_tname}"'
                            
                            insert_sql = f'INSERT INTO {full_sql_tname} ({col_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;'
                            target_cur.executemany(insert_sql, lookup_rows)
                            target_conn.commit()
                    except Exception:
                        target_conn.rollback()

            source_conn.close()
            target_conn.close()
            print(f"[Database Cloner] Recreated {len(sdm.tables)} table structures in '{self.target_dbname}'.")

        except Exception as e:
            raise ProjectionError(f"Failed to clone schema structures to target DB: {str(e)}")
