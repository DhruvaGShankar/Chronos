"""
Chronos Engine v2.1 Flagship Validation: OneApp Enterprise Simulation.
Simulates a multi-tenant enterprise OneApp platform schema with zero OneApp-specific hardcoded Python kernel logic.
Demonstrates Schema Intelligence, Simulation Hashes, Causal Replay, Root-Cause Explanation, and Data Projection.
"""

import sys
import os
import sqlite3
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chronos.introspection.sql import SQLDDLIntrospector
from chronos.introspection.intelligence import SchemaIntelligenceEngine
from chronos.enrichment.engine import SemanticEnrichmentEngine
from chronos.compiler.compiler import ChronosCompiler
from chronos.runtime.kernel import SimulationKernel
from chronos.observability.replay import TimeTravelReplayEngine
from chronos.observability.causal import CausalExplainerEngine
from chronos.projection.sqlite import SQLiteMaterializer
from chronos.projection.parquet import ParquetProjectionAdapter

def generate_oneapp_enterprise_ddl() -> str:
    """Generates the multi-tenant OneApp enterprise platform schema DDL."""
    return """
    CREATE TABLE TB_ONEAPP_ORGANIZATION (
        org_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        plan_tier TEXT NOT NULL
    );

    CREATE TABLE TB_ONEAPP_TENANT (
        tenant_id TEXT PRIMARY KEY,
        org_id TEXT REFERENCES TB_ONEAPP_ORGANIZATION(org_id),
        subdomain TEXT NOT NULL,
        status TEXT NOT NULL
    );

    CREATE TABLE TB_ONEAPP_USER (
        user_id TEXT PRIMARY KEY,
        tenant_id TEXT REFERENCES TB_ONEAPP_TENANT(tenant_id),
        email TEXT NOT NULL,
        conscientiousness REAL,
        aptitude REAL,
        financial_stability REAL,
        role_type TEXT,
        status TEXT
    );

    CREATE TABLE TB_ONEAPP_SUBSCRIPTION (
        sub_id TEXT PRIMARY KEY,
        tenant_id TEXT REFERENCES TB_ONEAPP_TENANT(tenant_id),
        monthly_fee REAL,
        auto_renew INTEGER
    );

    CREATE TABLE TB_ONEAPP_WORKSPACE (
        workspace_id TEXT PRIMARY KEY,
        tenant_id TEXT REFERENCES TB_ONEAPP_TENANT(tenant_id),
        workspace_name TEXT NOT NULL
    );

    CREATE TABLE TB_ONEAPP_PROJECT (
        project_id TEXT PRIMARY KEY,
        workspace_id TEXT REFERENCES TB_ONEAPP_WORKSPACE(workspace_id),
        project_code TEXT NOT NULL,
        budget REAL
    );

    CREATE TABLE TB_ONEAPP_DOCUMENT (
        doc_id TEXT PRIMARY KEY,
        project_id TEXT REFERENCES TB_ONEAPP_PROJECT(project_id),
        author_user_id TEXT REFERENCES TB_ONEAPP_USER(user_id),
        title TEXT NOT NULL,
        version_num INTEGER
    );

    CREATE TABLE TB_ONEAPP_ACTIVITY_LOG (
        activity_id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES TB_ONEAPP_USER(user_id),
        project_id TEXT REFERENCES TB_ONEAPP_PROJECT(project_id),
        activity_type TEXT NOT NULL,
        timestamp TEXT
    );

    CREATE TABLE TB_ONEAPP_BILLING_INVOICE (
        invoice_id TEXT PRIMARY KEY,
        sub_id TEXT REFERENCES TB_ONEAPP_SUBSCRIPTION(sub_id),
        amount_due REAL,
        status TEXT
    );

    CREATE TABLE TB_ONEAPP_PAYMENT_TRANSACTION (
        payment_id TEXT PRIMARY KEY,
        invoice_id TEXT REFERENCES TB_ONEAPP_BILLING_INVOICE(invoice_id),
        amount_paid REAL,
        payment_date TEXT
    );
    """

def run_oneapp_flagship_simulation():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oneapp_enterprise.db")
    parquet_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oneapp_parquet_data")

    if os.path.exists(db_file):
        os.remove(db_file)

    print("==========================================================================")
    print(" CHRONOS ENGINE v2.1 FLAGSHIP VALIDATION: ONEAPP ENTERPRISE WORKLOAD")
    print("==========================================================================")

    # 1. Setup & Schema Introspection
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    ddl_sql = generate_oneapp_enterprise_ddl()
    cursor.executescript(ddl_sql)
    conn.commit()

    t0_intro = time.perf_counter()
    introspector = SQLDDLIntrospector(domain_name="OneApp_Enterprise_Platform")
    sdm = introspector.inspect(ddl_sql)
    intel = SchemaIntelligenceEngine.analyze_schema_intelligence(sdm)
    t1_intro = time.perf_counter()

    print(f"\n[Phase 1: Introspection & Schema Intelligence] Introspected {len(sdm.tables)} tables in {(t1_intro - t0_intro)*1000:.2f} ms")
    print(f"  * Topological Execution Ordering: {sdm.dependency_dag}")
    print(f"  * Discovered Module Prefixes: {list(intel['module_groups'].keys())}")
    print(f"  * Discovered Lifecycle State Columns: {list(intel['lifecycle_columns'].keys())}")

    # 2. Semantic Enrichment & Compilation
    t0_comp = time.perf_counter()
    enricher = SemanticEnrichmentEngine()
    bdm = enricher.enrich(sdm)
    compiler = ChronosCompiler(root_seed=99999)
    ir = compiler.compile(bdm)
    t1_comp = time.perf_counter()

    print(f"\n[Phase 2: Compiler Lowering] Generated Chronos IR v2.1 in {(t1_comp - t0_comp)*1000:.2f} ms")
    print(f"  * Simulation ID: {ir.header.simulation_id}")
    print(f"  * Cryptographic Source Schema Hash: {ir.header.source_schema_hash[:16]}...")
    print(f"  * Cryptographic Semantic Model Hash: {ir.header.semantic_model_hash[:16]}...")

    # 3. Deterministic Runtime Execution
    sim_ticks = 90
    kernel = SimulationKernel(ir)
    kernel.bootstrap_world({"TB_ONEAPP_ORGANIZATION": 2, "TB_ONEAPP_USER": 10, "TB_ONEAPP_PROJECT": 4})

    t0_sim = time.perf_counter()
    events = kernel.run_simulation(ticks=sim_ticks)
    t1_sim = time.perf_counter()

    sim_duration = t1_sim - t0_sim
    throughput = len(events) / sim_duration if sim_duration > 0 else 0

    print(f"\n[Phase 3: Simulation Kernel Execution] Ran {sim_ticks} Ticks in {sim_duration:.3f} s")
    print(f"  * Total Causal Events Emitted: {len(events):,}")
    print(f"  * Simulation Kernel Engine Speed: {throughput:,.0f} Events / Sec")

    # 4. Observability & Time-Travel Replay Engine
    target_replay_tick = 30
    initial_snapshot = {"TB_ONEAPP_USER": kernel.state_store.get_entities("TB_ONEAPP_USER")}
    replayed_state = TimeTravelReplayEngine.replay_state_at_tick(events, initial_snapshot, target_replay_tick)
    print(f"\n[Phase 4: Time-Travel State Replay] Reconstructed world state snapshot at Tick {target_replay_tick}")
    print(f"  * Replayed User Records at Tick {target_replay_tick}: {len(replayed_state.get('TB_ONEAPP_USER', []))} users")

    # 5. Diagnostic Root-Cause Causal Explainer
    target_user = "tb_oneapp_user_001"
    user_history = CausalExplainerEngine.explain_entity_state(events, target_user)
    report = CausalExplainerEngine.format_explanation_report(target_user, user_history[:5])
    print(f"\n[Phase 5: Diagnostic Causal Explainer]")
    print(report)

    # 6. Projection Engine Exports (SQLite & Parquet Data Lake)
    t0_proj = time.perf_counter()
    SQLiteMaterializer().materialize(kernel.state_store.get_all(), events, conn)
    ParquetProjectionAdapter().project(kernel.state_store.get_all(), events, parquet_dir)
    t1_proj = time.perf_counter()

    print(f"\n[Phase 6: Projection Engine Exports] Projected data to SQLite and Parquet in {(t1_proj - t0_proj)*1000:.2f} ms")
    print("==========================================================================")
    print(" CHRONOS v2.1 ONEAPP ENTERPRISE VALIDATION: COMPLETED CLEANLY")
    print("==========================================================================")

    conn.close()

if __name__ == "__main__":
    run_oneapp_flagship_simulation()
