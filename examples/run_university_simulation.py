"""
Example Script: Running a Full University Simulation with Chronos Engine.
"""

import sys
import os

# Put package in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chronos.introspection.sql_ddl import SQLDDLIntrospector
from chronos.enrichment.engine import SemanticEnrichmentEngine
from chronos.compiler.compiler import ChronosCompiler
from chronos.runtime.kernel import SimulationKernel
from chronos.materialization.sql_dump import SQLDumpMaterializer
from chronos.materialization.csv_writer import CSVMaterializer
from chronos.materialization.json_writer import JSONMaterializer

def run_university_demo():
    university_sql_ddl = """
    CREATE TABLE TB_FACULTY (
        faculty_id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(100) NOT NULL
    );

    CREATE TABLE TB_STUDENT (
        student_id VARCHAR(36) PRIMARY KEY,
        cgpa FLOAT,
        attendance_pct FLOAT,
        fee_status VARCHAR(20),
        placement_eligible BOOLEAN
    );

    CREATE TABLE TB_ATTENDANCE (
        attendance_id VARCHAR(36) PRIMARY KEY,
        student_id VARCHAR(36) REFERENCES TB_STUDENT(student_id),
        timestamp DATETIME,
        is_present BOOLEAN
    );

    CREATE TABLE TB_EXAM_RESULT (
        result_id VARCHAR(36) PRIMARY KEY,
        student_id VARCHAR(36) REFERENCES TB_STUDENT(student_id),
        score FLOAT
    );
    """

    print("--- CHRONOS ENGINE DEMO: UNIVERSITY ORGANIZATIONAL SIMULATION ---")
    
    # 1. Introspect Schema
    introspector = SQLDDLIntrospector(domain_name="UniversityDomain")
    sdm = introspector.inspect(university_sql_ddl)
    print(f"1. Schema Introspective AST Built ({len(sdm.tables)} tables extracted).")

    # 2. Enrich Behaviorally
    enricher = SemanticEnrichmentEngine()
    bdm = enricher.enrich(sdm)
    print(f"2. Semantic Behavioral AST Enriched with {len(bdm.personas)} persona vectors and invariant rules.")

    # 3. Compile to Chronos IR
    compiler = ChronosCompiler(root_seed=424242)
    ir = compiler.compile(bdm)
    print(f"3. Compiled Chronos IR Execution Plan (Seed: {ir.seed_root}).")

    # 4. Execute Simulation Kernel
    kernel = SimulationKernel(ir)
    kernel.bootstrap_world(entity_counts={"TB_FACULTY": 3, "TB_STUDENT": 10})
    events = kernel.run_simulation(ticks=90)
    print(f"4. Simulation Executed for 90 Days ({len(events)} events generated).")

    # 5. Materialize Data
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    SQLDumpMaterializer().materialize(kernel.state_store.get_all(), events, os.path.join(out_dir, "university_seed.sql"))
    CSVMaterializer().materialize(kernel.state_store.get_all(), events, os.path.join(out_dir, "csv"))
    JSONMaterializer().materialize(kernel.state_store.get_all(), events, os.path.join(out_dir, "simulation.json"))

    print("\n--- SIMULATION COMPLETED SUCCESSFULLY ---")

if __name__ == "__main__":
    run_university_demo()
