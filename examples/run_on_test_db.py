"""
End-to-End Demonstration: Running Chronos Engine on a Live Test SQLite Database.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chronos.introspection.sqlite_introspector import SQLiteIntrospector
from chronos.enrichment.engine import SemanticEnrichmentEngine
from chronos.compiler.compiler import ChronosCompiler
from chronos.runtime.kernel import SimulationKernel
from chronos.materialization.sqlite_writer import SQLiteMaterializer

def run_test_database_simulation():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_enterprise.db")
    
    # Remove existing db if present for a clean run
    if os.path.exists(db_file):
        os.remove(db_file)

    print("==========================================================================")
    print(" CHRONOS SIMULATION ENGINE: LIVE TEST DATABASE RUN")
    print("==========================================================================")

    # STEP 1: Bootstrap Target Enterprise Database Schema
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE TB_DEPARTMENT (
        dept_id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );

    CREATE TABLE TB_STUDENT (
        student_id TEXT PRIMARY KEY,
        dept_id TEXT REFERENCES TB_DEPARTMENT(dept_id),
        cgpa REAL,
        attendance_pct REAL,
        fee_status TEXT,
        placement_eligible INTEGER
    );

    CREATE TABLE TB_ATTENDANCE (
        attendance_id TEXT PRIMARY KEY,
        student_id TEXT REFERENCES TB_STUDENT(student_id),
        timestamp TEXT,
        is_present INTEGER
    );

    CREATE TABLE TB_EXAM_RESULT (
        result_id TEXT PRIMARY KEY,
        student_id TEXT REFERENCES TB_STUDENT(student_id),
        score REAL
    );
    """)
    conn.commit()
    print(f"[Phase 1] Initialized clean SQLite database schema at: {db_file}")

    # STEP 2: Introspect Schema from Live SQLite Database Connection
    print("[Phase 2] Introspecting schema directly from SQLite database connection...")
    introspector = SQLiteIntrospector(domain_name="Live_SQLite_Domain")
    sdm = introspector.inspect(conn)

    for tname, tdef in sdm.tables.items():
        print(f"  - Table Introspected: {tname:<15} | Role: {tdef.inferred_role.value:<10} | Columns: {list(tdef.columns.keys())}")

    # STEP 3: Semantic Enrichment & IR Compilation
    print("\n[Phase 3] Enriching AST and Compiling Chronos IR Plan...")
    enricher = SemanticEnrichmentEngine()
    bdm = enricher.enrich(sdm)
    compiler = ChronosCompiler(root_seed=9999)
    ir = compiler.compile(bdm)

    # STEP 4: Execute Deterministic Simulation Kernel
    print("[Phase 4] Executing Discrete Event Simulation Kernel for 90 Days...")
    kernel = SimulationKernel(ir)
    kernel.bootstrap_world(entity_counts={"TB_DEPARTMENT": 1, "TB_STUDENT": 8})
    event_log = kernel.run_simulation(ticks=90)
    print(f"  - Simulation Completed. Emitted {len(event_log)} events.")

    # STEP 5: Materialize Simulated Data DIRECTLY INTO SQLite DB
    print("\n[Phase 5] Materializing simulated state directly into target SQLite database...")
    SQLiteMaterializer().materialize(kernel.state_store.get_all(), event_log, conn)

    # STEP 6: Execute Real SQL Queries Against the Live Materialized Database
    print("\n==========================================================================")
    print(" EXECUTING SQL QUERIES DIRECTLY AGAINST 'test_enterprise.db'")
    print("==========================================================================")
    
    query = """
    SELECT student_id, cgpa, attendance_pct, fee_status, placement_eligible
    FROM TB_STUDENT
    ORDER BY cgpa DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    print(f"{'Student ID':<15} | {'CGPA':<5} | {'Att. %':<6} | {'Fee Status':<10} | {'Placement Status'}")
    print("-" * 65)
    for r in rows:
        s_id, cgpa, att, fee, eligible = r
        status = "ELIGIBLE" if eligible == 1 else "DISQUALIFIED"
        print(f"{s_id:<15} | {cgpa:<5.2f} | {att*100:<5.1f}% | {fee:<10} | {status}")
    print("==========================================================================")

    conn.close()

if __name__ == "__main__":
    run_test_database_simulation()
