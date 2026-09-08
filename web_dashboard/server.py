"""
Chronos Engine v2.1 - Web Dashboard API Backend Server.
Provides REST API endpoints for Live PostgreSQL Introspection, Chronos IR Compilation, Simulation Execution, and Data Exports.
"""

import sys
import os
import json
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Add package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chronos.introspection.sql import SQLDDLIntrospector
from chronos.introspection.postgresql import PostgreSQLIntrospector
from chronos.introspection.intelligence import SchemaIntelligenceEngine
from chronos.enrichment.engine import SemanticEnrichmentEngine
from chronos.compiler.compiler import ChronosCompiler
from chronos.runtime.kernel import SimulationKernel
from chronos.observability.replay import TimeTravelReplayEngine
from chronos.observability.causal import CausalExplainerEngine
from chronos.materialization.sql_dump import SQLDumpMaterializer

PORT = 8080
WEB_DIR = os.path.dirname(os.path.abspath(__file__))

class ChronosAPIRequestHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler providing static web files and REST API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_POST(self):
        url = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_length)
        
        try:
            body = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
        except Exception:
            body = {}

        if url.path == "/api/introspect":
            self.handle_introspect(body)
        elif url.path == "/api/postgres_introspect":
            self.handle_postgres_introspect(body)
        elif url.path == "/api/compile":
            self.handle_compile(body)
        elif url.path == "/api/simulate":
            self.handle_simulate(body)
        else:
            self.send_error(404, "API endpoint not found")

    def handle_introspect(self, body):
        sql_ddl = body.get("sql_ddl", "")
        domain_name = body.get("domain_name", "EnterpriseDomain")
        
        try:
            introspector = SQLDDLIntrospector(domain_name=domain_name)
            sdm = introspector.inspect(sql_ddl)
            
            tables_summary = []
            for tname, tdef in sdm.tables.items():
                tables_summary.append({
                    "name": tname,
                    "role": tdef.inferred_role.value,
                    "columns": list(tdef.columns.keys()),
                    "foreign_keys": tdef.foreign_keys
                })

            response = {
                "success": True,
                "domain_name": sdm.domain_name,
                "tables": tables_summary,
                "dependency_dag": sdm.dependency_dag
            }
            self.send_json_response(response)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, status=400)

    def handle_postgres_introspect(self, body):
        host = body.get("host", "localhost")
        port = body.get("port", 5432)
        dbname = body.get("dbname", "XSC_DB_ONEAPP_TEST")
        user = body.get("user", "postgres")
        password = body.get("password", "postgres")

        try:
            import psycopg2
            conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
            introspector = PostgreSQLIntrospector(domain_name=dbname)
            sdm = introspector.inspect(conn)
            intel = SchemaIntelligenceEngine.analyze_schema_intelligence(sdm)

            tables_summary = []
            for tname, tdef in list(sdm.tables.items())[:30]:  # Return sample 30 tables
                tables_summary.append({
                    "name": tname,
                    "role": tdef.inferred_role.value,
                    "columns": list(tdef.columns.keys()),
                    "foreign_keys": tdef.foreign_keys
                })

            response = {
                "success": True,
                "domain_name": dbname,
                "total_tables": len(sdm.tables),
                "sample_tables": tables_summary,
                "dependency_dag": sdm.dependency_dag,
                "module_groups": list(intel["module_groups"].keys())
            }
            conn.close()
            self.send_json_response(response)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, status=400)

    def handle_compile(self, body):
        sql_ddl = body.get("sql_ddl", "")
        seed = body.get("seed", 1337)
        
        try:
            sdm = SQLDDLIntrospector("EnterpriseDomain").inspect(sql_ddl)
            bdm = SemanticEnrichmentEngine().enrich(sdm)
            ir = ChronosCompiler(root_seed=seed).compile(bdm)

            response = {
                "success": True,
                "ir": {
                    "ir_header": {
                        "ir_version": ir.header.ir_version if ir.header else "2.1.0",
                        "simulation_id": ir.header.simulation_id if ir.header else "sim_0x1337",
                        "source_schema_hash": ir.header.source_schema_hash if ir.header else "",
                        "semantic_model_hash": ir.header.semantic_model_hash if ir.header else ""
                    },
                    "execution_topology": ir.execution_topology,
                    "entities": ir.entities,
                    "state_machines": ir.state_machines,
                    "rules": ir.rules,
                    "schedules": ir.schedules
                }
            }
            self.send_json_response(response)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, status=400)

    def handle_simulate(self, body):
        sql_ddl = body.get("sql_ddl", "")
        seed = body.get("seed", 1337)
        ticks = body.get("ticks", 90)
        entity_counts = body.get("entity_counts", {"TB_STUDENT": 8, "TB_CUSTOMER": 8, "TB_SHOPPER": 8})

        try:
            sdm = SQLDDLIntrospector("EnterpriseDomain").inspect(sql_ddl)
            bdm = SemanticEnrichmentEngine().enrich(sdm)
            ir = ChronosCompiler(root_seed=seed).compile(bdm)

            kernel = SimulationKernel(ir)
            kernel.bootstrap_world(entity_counts)
            
            import time
            t0 = time.perf_counter()
            events = kernel.run_simulation(ticks=ticks)
            t1 = time.perf_counter()

            exec_time_sec = t1 - t0
            events_count = len(events)
            events_per_sec = events_count / exec_time_sec if exec_time_sec > 0 else 0

            response = {
                "success": True,
                "metrics": {
                    "ticks": ticks,
                    "total_events": events_count,
                    "exec_time_ms": round(exec_time_sec * 1000, 2),
                    "events_per_sec": round(events_per_sec, 0),
                    "simulation_id": ir.header.simulation_id if ir.header else "sim_0x1337"
                },
                "entity_store": kernel.state_store.get_all(),
                "event_log_sample": [
                    {
                        "event_id": e.event_id,
                        "tick": e.tick,
                        "actor_id": e.actor_id,
                        "target_id": e.target_id,
                        "event_type": e.event_type,
                        "payload": e.payload
                    } for e in events[:50]
                ]
            }
            self.send_json_response(response)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, status=400)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, ChronosAPIRequestHandler)
    print(f"==========================================================================")
    print(f" CHRONOS WEB DASHBOARD SERVER RUNNING AT: http://localhost:{PORT}")
    print(f"==========================================================================")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
