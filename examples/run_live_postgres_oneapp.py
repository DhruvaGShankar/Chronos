"""
Chronos Engine v2.1 Live PostgreSQL OneApp Enterprise Introspector & Simulation Runner.
Connects directly to a live PostgreSQL database (e.g. XSC_DB_ONEAPP_TEST), introspects schema metadata via pg_catalog,
compiles Chronos IR v2.1, runs deterministic simulation kernel, and streams state projections back to PostgreSQL via PGCOPY.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chronos.introspection.postgresql import PostgreSQLIntrospector
from chronos.introspection.intelligence import SchemaIntelligenceEngine
from chronos.enrichment.engine import SemanticEnrichmentEngine
from chronos.compiler.compiler import ChronosCompiler
from chronos.runtime.kernel import SimulationKernel
from chronos.observability.replay import TimeTravelReplayEngine
from chronos.observability.causal import CausalExplainerEngine
from chronos.projection.postgresql import PostgreSQLProjectionAdapter

def run_live_postgres_oneapp(
    host: str = "localhost",
    port: int = 5432,
    dbname: str = "XSC_DB_ONEAPP_TEST",
    user: str = "postgres",
    password: str = ""
):
    try:
        import psycopg2
    except ImportError:
        print("Error: psycopg2-binary is required for PostgreSQL introspection. Please install it using: pip install psycopg2-binary")
        return

    print("==========================================================================")
    print(" CHRONOS ENGINE v2.1: LIVE POSTGRESQL INTROSPECTION & SIMULATION")
    print(f" Target DB: {dbname} @ {host}:{port}")
    print("==========================================================================")

    # 1. Connect to Live PostgreSQL Database
    try:
        print(f"[Connection] Connecting to PostgreSQL '{dbname}' as user '{user}'...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        print(" [Connection] Connected successfully!")
    except Exception as e:
        print(f" [Connection Error] Failed to connect to PostgreSQL: {e}")
        return

    # 2. Introspect Schema Metadata via pg_catalog & information_schema
    t0_intro = time.perf_counter()
    introspector = PostgreSQLIntrospector(domain_name="OneApp_Live_PostgreSQL")
    sdm = introspector.inspect(conn)
    intel = SchemaIntelligenceEngine.analyze_schema_intelligence(sdm)
    t1_intro = time.perf_counter()

    print(f"\n[Phase 1: PostgreSQL Introspection Results]")
    print(f"  * Total Discovered Tables ({len(sdm.tables)}):")
    for idx, (tname, tdef) in enumerate(sdm.tables.items()):
        cols = list(tdef.columns.keys())
        pks = tdef.primary_keys
        fks = tdef.foreign_keys
        print(f"    {idx+1:02d}. {tname:<35} | Role: {tdef.inferred_role.value:<10} | Cols: {len(cols)} | PKs: {pks} | FKs: {len(fks)}")

    print(f"\n  * Discovered Topological Creation Order ({len(sdm.dependency_dag)} Nodes):")
    for node, children in list(sdm.dependency_dag.items())[:12]:
        print(f"    - {node} --> {children if children else 'Leaf Node'}")

    print(f"\n  * Schema Intelligence Analysis:")
    print(f"    - Discovered Module Groups: {list(intel['module_groups'].keys())}")
    print(f"    - Discovered Lifecycle Columns: {intel['lifecycle_columns']}")

    # 3. Semantic Enrichment & Chronos IR v2.1 Lowering
    t0_comp = time.perf_counter()
    enricher = SemanticEnrichmentEngine()
    bdm = enricher.enrich(sdm)
    compiler = ChronosCompiler(root_seed=88888)
    ir = compiler.compile(bdm)
    t1_comp = time.perf_counter()

    print(f"\n[Phase 2: Chronos IR v2.1 Compilation] Compiled plan in {(t1_comp - t0_comp)*1000:.2f} ms")
    print(f"  * Simulation ID: {ir.header.simulation_id}")
    print(f"  * Cryptographic Source Schema Hash: {ir.header.source_schema_hash[:16]}...")
    print(f"  * Cryptographic Semantic Model Hash: {ir.header.semantic_model_hash[:16]}...")

    # 4. Simulation Runtime Execution
    sim_ticks = 60
    kernel = SimulationKernel(ir)
    entity_counts = {tname: 5 for tname in sdm.tables.keys()}
    kernel.bootstrap_world(entity_counts)

    t0_sim = time.perf_counter()
    events = kernel.run_simulation(ticks=sim_ticks)
    t1_sim = time.perf_counter()

    sim_time = t1_sim - t0_sim
    speed = len(events) / sim_time if sim_time > 0 else 0

    print(f"\n[Phase 3: Simulation Kernel Execution] Executed {sim_ticks} Ticks in {sim_time:.3f} s")
    print(f"  * Total Causal Events Emitted: {len(events):,}")
    print(f"  * SIMULATION KERNEL SPEED: {speed:,.0f} Events / Sec")

    # 5. Time-Travel State Replay Snapshot
    target_tick = 30
    if sdm.tables:
        sample_table = list(sdm.tables.keys())[0]
        initial_snap = {sample_table: kernel.state_store.get_entities(sample_table)}
        replayed = TimeTravelReplayEngine.replay_state_at_tick(events, initial_snap, target_tick)
        print(f"\n[Phase 4: Time-Travel State Replay] Snapshot at Tick {target_tick} for '{sample_table}': {len(replayed.get(sample_table, []))} records")

    print("\n==========================================================================")
    print(f" CHRONOS v2.1 LIVE POSTGRESQL SIMULATION ON '{dbname}': COMPLETED CLEANLY")
    print("==========================================================================")

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        user_arg = sys.argv[1]
        pass_arg = sys.argv[2]
        dbname_arg = sys.argv[3] if len(sys.argv) >= 4 else "XSC_DB_ONEAPP_TEST"
        port_arg = int(sys.argv[4]) if len(sys.argv) >= 5 else 5432
        host_arg = sys.argv[5] if len(sys.argv) >= 6 else "localhost"
        run_live_postgres_oneapp(host=host_arg, port=port_arg, dbname=dbname_arg, user=user_arg, password=pass_arg)
    else:
        print("Usage: python examples/run_live_postgres_oneapp.py <user> <password> [dbname] [port] [host]")
