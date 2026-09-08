"""
Chronos Engine v2.1 Master End-to-End Execution & Validation Runner.
Introspects live PostgreSQL database (XSC_DB_ONEAPP_TEST), compiles Chronos IR v2.1, runs deterministic simulation,
verifies source DB isolation, projects dataset into target database (XSC_DB_ONEAPP_SIM), runs validation suite,
and executes bit-exact determinism tests.
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
from chronos.observability.validator import ChronosValidatorSuite
from chronos.projection.pg_cloning import PostgreSQLDatabaseCloner
from chronos.projection.postgresql import PostgreSQLProjectionAdapter

def get_source_row_counts(conn, sdm) -> dict:
    """Helper to record table row counts in source database."""
    cur = conn.cursor()
    counts = {}
    for tname in sdm.tables.keys():
        schema_prefix = f'"{tname.split(".")[0]}"."' if "." in tname else '"public"."'
        bare_tname = tname.split(".")[-1]
        full_sql_tname = f'{schema_prefix}{bare_tname}"'
        try:
            cur.execute(f'SELECT count(*) FROM {full_sql_tname};')
            counts[tname] = cur.fetchone()[0]
        except Exception:
            conn.rollback()
            counts[tname] = 0
    return counts

def run_oneapp_full_pipeline(
    user: str = "postgres",
    password: str = "postgres",
    source_dbname: str = "XSC_DB_ONEAPP_TEST",
    target_dbname: str = "XSC_DB_ONEAPP_SIM",
    port: int = 5432,
    host: str = "localhost"
):
    try:
        import psycopg2
    except ImportError:
        print("Error: psycopg2-binary required.")
        return

    print("==========================================================================")
    print(" CHRONOS ENGINE v2.1: END-TO-END ONEAPP SYNTHETIC SEEDING & VALIDATION")
    print(f" Source DB (Read-Only): {source_dbname} @ {host}:{port}")
    print(f" Target DB (Isolated):  {target_dbname} @ {host}:{port}")
    print("==========================================================================")

    t_start = time.perf_counter()

    # STEP 1: Connect to Source Database & Record Pre-Run Row Counts
    t0_conn = time.perf_counter()
    source_conn = psycopg2.connect(host=host, port=port, dbname=source_dbname, user=user, password=password)
    t1_conn = time.perf_counter()
    print(f"[Phase 1: Connection] Connected to source '{source_dbname}' in {(t1_conn - t0_conn)*1000:.2f} ms")

    # STEP 2: Schema Introspection & Schema Intelligence
    t0_intro = time.perf_counter()
    introspector = PostgreSQLIntrospector(domain_name="OneApp_Enterprise")
    sdm = introspector.inspect(source_conn)
    intel = SchemaIntelligenceEngine.analyze_schema_intelligence(sdm)
    t1_intro = time.perf_counter()

    source_pre_counts = get_source_row_counts(source_conn, sdm)
    print(f"[Phase 2: Introspection] Introspected {len(sdm.tables)} tables in {(t1_intro - t0_intro)*1000:.2f} ms")
    print(f"  * Discovered Module Prefixes: {list(intel['module_groups'].keys())}")

    # STEP 3: Semantic Enrichment & Chronos IR v2.1 Lowering (Run A: Seed 1337)
    t0_comp = time.perf_counter()
    enricher = SemanticEnrichmentEngine()
    bdm_a = enricher.enrich(sdm)
    compiler = ChronosCompiler(root_seed=1337)
    ir_a = compiler.compile(bdm_a)
    t1_comp = time.perf_counter()

    print(f"[Phase 3: IR Compilation] Compiled Chronos IR v2.1 in {(t1_comp - t0_comp)*1000:.2f} ms")
    print(f"  * Simulation ID (Run A): {ir_a.header.simulation_id}")
    print(f"  * Source Schema Hash: {ir_a.header.source_schema_hash[:16]}...")
    print(f"  * Semantic Model Hash: {ir_a.header.semantic_model_hash[:16]}...")

    # STEP 4: Simulation Runtime Execution (Run A: Seed 1337)
    sim_ticks = 90
    kernel_a = SimulationKernel(ir_a)
    entity_counts = {tname: 5 for tname in sdm.tables.keys()}
    kernel_a.bootstrap_world(entity_counts)

    t0_sim = time.perf_counter()
    events_a = kernel_a.run_simulation(ticks=sim_ticks)
    t1_sim = time.perf_counter()

    sim_duration_a = t1_sim - t0_sim
    events_per_sec_a = len(events_a) / sim_duration_a if sim_duration_a > 0 else 0

    print(f"[Phase 4: Simulation Kernel] Executed {sim_ticks} Ticks in {sim_duration_a:.3f} s")
    print(f"  * Causal Events Emitted: {len(events_a):,}")
    print(f"  * SIMULATION KERNEL THROUGHPUT: {events_per_sec_a:,.0f} Events / Sec")

    # STEP 5: Observability, Time-Travel Replay & Root-Cause Explainer
    target_tick = 30
    if sdm.tables:
        sample_tname = list(sdm.tables.keys())[0]
        initial_snap = {sample_tname: kernel_a.state_store.get_entities(sample_tname)}
        replayed_state = TimeTravelReplayEngine.replay_state_at_tick(events_a, initial_snap, target_tick)
        print(f"[Phase 5: Time-Travel Replay] Snapshot at Tick {target_tick} for '{sample_tname}': {len(replayed_state.get(sample_tname, []))} records")

    # STEP 6: Target Database Creation & DDL Schema Projection
    t0_clone = time.perf_counter()
    cloner = PostgreSQLDatabaseCloner(
        host=host, port=port, user=user, password=password, source_dbname=source_dbname, target_dbname=target_dbname
    )
    cloner.clone_schema_structures(sdm)
    t1_clone = time.perf_counter()
    print(f"[Phase 6: Schema Cloning] Created '{target_dbname}' table DDL in {(t1_clone - t0_clone)*1000:.2f} ms")

    # STEP 7: PostgreSQL Projection Engine Streaming (PGCOPY to XSC_DB_ONEAPP_SIM)
    t0_proj = time.perf_counter()
    target_conn = psycopg2.connect(host=host, port=port, dbname=target_dbname, user=user, password=password)
    PostgreSQLProjectionAdapter().project(kernel_a.state_store.get_all(), events_a, target_conn)
    t1_proj = time.perf_counter()

    proj_duration = t1_proj - t0_proj
    print(f"[Phase 7: Materialization] Projected synthetic data to '{target_dbname}' via PGCOPY in {proj_duration*1000:.2f} ms")

    # STEP 8: Source Database Safety Check (Verify XSC_DB_ONEAPP_TEST Untouched)
    source_post_counts = get_source_row_counts(source_conn, sdm)
    safety_report = ChronosValidatorSuite.validate_source_safety(source_pre_counts, source_post_counts)
    print(f"[Phase 8: Source Safety Check] Source Database '{source_dbname}' Untouched: {safety_report['status']}")

    # STEP 9: Structural & Simulation Validation
    struct_report = ChronosValidatorSuite.validate_target_structural_integrity(target_conn, sdm)
    sim_val_report = ChronosValidatorSuite.validate_simulation_events(events_a)
    print(f"[Phase 9: Structural & Simulation Validation]")
    print(f"  * Total Rows Materialized: {struct_report['total_rows_materialized']:,}")
    print(f"  * Populated Tables: {struct_report['populated_tables_count']} / {len(sdm.tables)}")
    print(f"  * Primary Key Violations: {struct_report['pk_violations']}")
    print(f"  * Non-Zero Causal Events Valid: {sim_val_report['non_zero_events']}")

    # STEP 10: Bit-Exact Determinism Verification (Run B: Seed 1337 vs Run C: Seed 1338)
    print(f"[Phase 10: Bit-Exact Determinism Test]")
    
    # Run B (Seed 1337)
    kernel_b = SimulationKernel(compiler.compile(enricher.enrich(sdm)))
    kernel_b.bootstrap_world(entity_counts)
    events_b = kernel_b.run_simulation(ticks=sim_ticks)

    # Run C (Seed 1338)
    compiler_c = ChronosCompiler(root_seed=1338)
    kernel_c = SimulationKernel(compiler_c.compile(enricher.enrich(sdm)))
    kernel_c.bootstrap_world(entity_counts)
    events_c = kernel_c.run_simulation(ticks=sim_ticks)

    det_report = ChronosValidatorSuite.validate_determinism(
        run_a_sim_id=ir_a.header.simulation_id,
        run_a_events=events_a,
        run_b_sim_id=kernel_b.ir.header.simulation_id,
        run_b_events=events_b,
        run_c_sim_id=kernel_c.ir.header.simulation_id,
        run_c_events=events_c
    )
    print(f"  * Same-Seed Bit-Exact Match (Seed 1337): {det_report['same_seed_match']}")
    print(f"  * Different-Seed Variance (Seed 1338): {det_report['different_seed_variant']}")
    print(f"  * Determinism Status: {det_report['status']}")

    t_end = time.perf_counter()
    total_time = t_end - t_start

    rows_per_sec = struct_report['total_rows_materialized'] / proj_duration if proj_duration > 0 else 0

    print("\n==========================================================================")
    print(" CHRONOS ENGINE v2.1 END-TO-END VERIFICATION DELIVERABLE SUMMARY")
    print("==========================================================================")
    print(f"  1. Number of Source Tables:                 {len(sdm.tables)}")
    print(f"  2. Number of Target Tables Populated:       {struct_report['populated_tables_count']}")
    print(f"  3. Number of Inferred Entities:             {len(sdm.tables)}")
    print(f"  4. Number of Behavioral Rules:              {len(ir_a.rules)}")
    print(f"  5. Number of Event Schedules:               {len(ir_a.schedules)}")
    print(f"  6. Number of Compiled IR Entities:          {len(ir_a.entities)}")
    print(f"  7. Simulation Duration:                     {sim_ticks} Ticks ({sim_duration_a:.3f} s)")
    print(f"  8. Number of Causal Events Emitted:         {len(events_a):,}")
    print(f"  9. Number of Generated Entities:            {sum(len(v) for v in kernel_a.state_store.get_all().values()):,}")
    print(f" 10. Total Generated Rows Materialized:       {struct_report['total_rows_materialized']:,}")
    print(f" 11. Simulation Kernel Speed:                 {events_per_sec_a:,.0f} Events / Sec")
    print(f" 12. PostgreSQL Materialization Speed:        {rows_per_sec:,.0f} Rows / Sec")
    print(f" 13. Target Structural Validation Status:     {struct_report['status']}")
    print(f" 14. Determinism Test Status:                 {det_report['status']}")
    print(f" 15. Source DB Untouched Safety Status:       {safety_report['status']}")
    print(f" 16. Total End-to-End Pipeline Latency:       {total_time:.3f} s")
    print("==========================================================================")

    source_conn.close()
    target_conn.close()

if __name__ == "__main__":
    run_oneapp_full_pipeline()
