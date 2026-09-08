"""
Chronos Engine v2.0 - 50+ Table Highly Normalized Enterprise ERP Performance Stress Test.
Measures Introspection speed, Topological Sort latency, IR Compilation time, and Simulation Kernel Throughput (Events/sec).
"""

import sys
import os
import time
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chronos.introspection.sqlite_introspector import SQLiteIntrospector
from chronos.enrichment.engine import SemanticEnrichmentEngine
from chronos.compiler.compiler import ChronosCompiler
from chronos.runtime.kernel import SimulationKernel
from chronos.materialization.sqlite_writer import SQLiteMaterializer

def generate_50_table_schema_ddl() -> str:
    """Generates a 50-table highly normalized ANSI SQL schema with deep foreign key dependency chains."""
    ddl_statements = []

    # Level 1: Root Enterprise Entities (Tables 1 - 5)
    ddl_statements.append("""
    CREATE TABLE TB_ENTERPRISE_GROUP (
        group_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        tax_id TEXT NOT NULL
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_LEGAL_ENTITY (
        entity_id TEXT PRIMARY KEY,
        group_id TEXT REFERENCES TB_ENTERPRISE_GROUP(group_id),
        country_code TEXT NOT NULL
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_CURRENCY (
        currency_code TEXT PRIMARY KEY,
        currency_name TEXT NOT NULL,
        symbol TEXT
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_REGION (
        region_id TEXT PRIMARY KEY,
        group_id TEXT REFERENCES TB_ENTERPRISE_GROUP(group_id),
        region_name TEXT NOT NULL
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_FACILITY_TYPE (
        type_id TEXT PRIMARY KEY,
        description TEXT NOT NULL
    );
    """)

    # Level 2: Organizational Divisions & Locations (Tables 6 - 15)
    for i in range(6, 16):
        ddl_statements.append(f"""
        CREATE TABLE TB_DIVISION_{i:02d} (
            division_id TEXT PRIMARY KEY,
            entity_id TEXT REFERENCES TB_LEGAL_ENTITY(entity_id),
            region_id TEXT REFERENCES TB_REGION(region_id),
            division_code TEXT NOT NULL
        );
        """)

    # Level 3: Department & Cost Center Hierarchy (Tables 16 - 25)
    for i in range(16, 26):
        parent_div = f"TB_DIVISION_{((i - 16) % 10) + 6:02d}"
        ddl_statements.append(f"""
        CREATE TABLE TB_DEPARTMENT_{i:02d} (
            dept_id TEXT PRIMARY KEY,
            division_id TEXT REFERENCES {parent_div}(division_id),
            cost_center_code TEXT NOT NULL
        );
        """)

    # Level 4: Positions, Grades, & Employee Master (Tables 26 - 35)
    ddl_statements.append("""
    CREATE TABLE TB_JOB_GRADE (
        grade_id TEXT PRIMARY KEY,
        grade_name TEXT NOT NULL,
        min_salary REAL,
        max_salary REAL
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_EMPLOYEE (
        emp_id TEXT PRIMARY KEY,
        dept_id TEXT REFERENCES TB_DEPARTMENT_16(dept_id),
        grade_id TEXT REFERENCES TB_JOB_GRADE(grade_id),
        conscientiousness REAL,
        aptitude REAL,
        financial_stability REAL,
        salary REAL,
        status TEXT
    );
    """)

    for i in range(28, 36):
        ddl_statements.append(f"""
        CREATE TABLE TB_EMP_BENEFIT_{i:02d} (
            benefit_id TEXT PRIMARY KEY,
            emp_id TEXT REFERENCES TB_EMPLOYEE(emp_id),
            benefit_type TEXT NOT NULL,
            coverage_amt REAL
        );
        """)

    # Level 5: Projects, Tasks, & Operational Activity (Tables 36 - 45)
    ddl_statements.append("""
    CREATE TABLE TB_PROJECT (
        project_id TEXT PRIMARY KEY,
        dept_id TEXT REFERENCES TB_DEPARTMENT_16(dept_id),
        project_code TEXT NOT NULL,
        budget REAL
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_PROJECT_TASK (
        task_id TEXT PRIMARY KEY,
        project_id TEXT REFERENCES TB_PROJECT(project_id),
        assigned_emp_id TEXT REFERENCES TB_EMPLOYEE(emp_id),
        task_name TEXT NOT NULL,
        est_hours REAL
    );
    """)

    for i in range(38, 46):
        ddl_statements.append(f"""
        CREATE TABLE TB_WORK_LOG_{i:02d} (
            log_id TEXT PRIMARY KEY,
            task_id TEXT REFERENCES TB_PROJECT_TASK(task_id),
            emp_id TEXT REFERENCES TB_EMPLOYEE(emp_id),
            hours_logged REAL,
            log_date TEXT
        );
        """)

    # Level 6: Ledger, Invoices, & Financial Audits (Tables 46 - 50)
    ddl_statements.append("""
    CREATE TABLE TB_CUSTOMER_ACCOUNT (
        cust_acc_id TEXT PRIMARY KEY,
        entity_id TEXT REFERENCES TB_LEGAL_ENTITY(entity_id),
        account_name TEXT NOT NULL
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_INVOICE (
        invoice_id TEXT PRIMARY KEY,
        cust_acc_id TEXT REFERENCES TB_CUSTOMER_ACCOUNT(cust_acc_id),
        total_amt REAL,
        status TEXT
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_INVOICE_LINE_ITEM (
        line_id TEXT PRIMARY KEY,
        invoice_id TEXT REFERENCES TB_INVOICE(invoice_id),
        amount REAL,
        description TEXT
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_PAYMENT_RECEIPT (
        receipt_id TEXT PRIMARY KEY,
        invoice_id TEXT REFERENCES TB_INVOICE(invoice_id),
        amount_paid REAL,
        payment_date TEXT
    );
    """)

    ddl_statements.append("""
    CREATE TABLE TB_AUDIT_LOG (
        audit_id TEXT PRIMARY KEY,
        receipt_id TEXT REFERENCES TB_PAYMENT_RECEIPT(receipt_id),
        timestamp TEXT,
        action TEXT
    );
    """)

    return "\n".join(ddl_statements)

def run_50_table_stress_test():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "50_table_enterprise.db")
    
    if os.path.exists(db_file):
        os.remove(db_file)

    print("==========================================================================")
    print(" CHRONOS ENGINE v2.0 PERFORMANCE BENCHMARK: 50+ TABLE NORMALIZED DB")
    print("==========================================================================")

    # STEP 1: Generate & Initialize Database Schema
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    t0_schema = time.perf_counter()
    schema_sql = generate_50_table_schema_ddl()
    cursor.executescript(schema_sql)
    conn.commit()
    t1_schema = time.perf_counter()
    print(f"[Setup] Generated 50-Table Schema DDL in {(t1_schema - t0_schema)*1000:.2f} ms")

    # STEP 2: Subsystem 1 Introspection Benchmarking
    t0_intro = time.perf_counter()
    introspector = SQLiteIntrospector(domain_name="50_Table_Enterprise_ERP")
    sdm = introspector.inspect(conn)
    t1_intro = time.perf_counter()
    
    num_tables = len(sdm.tables)
    total_fks = sum(len(t.foreign_keys) for t in sdm.tables.values())
    print(f"[Phase 1: Introspection] Introspected {num_tables} tables & {total_fks} FK constraints in {(t1_intro - t0_intro)*1000:.2f} ms")

    # STEP 3: Subsystem 2 Semantic Enrichment Benchmarking
    t0_enrich = time.perf_counter()
    enricher = SemanticEnrichmentEngine()
    bdm = enricher.enrich(sdm)
    t1_enrich = time.perf_counter()
    print(f"[Phase 2: Enrichment] Semantic AST Enriched in {(t1_enrich - t0_enrich)*1000:.2f} ms")

    # STEP 4: Subsystem 3 IR Compilation & Topological Sort Benchmarking
    t0_comp = time.perf_counter()
    compiler = ChronosCompiler(root_seed=55555)
    ir = compiler.compile(bdm)
    t1_comp = time.perf_counter()
    print(f"[Phase 3: IR Compilation] Topological DAG lowered to Chronos IR in {(t1_comp - t0_comp)*1000:.2f} ms")
    print(f"  - Topological Order (First 8 Nodes): {ir.execution_topology[:8]} ...")

    # STEP 5: Subsystem 4 Discrete Event Simulation Kernel Benchmarking
    kernel = SimulationKernel(ir)
    kernel.bootstrap_world({"TB_EMPLOYEE": 20, "TB_PROJECT": 5})

    sim_ticks = 180  # 180 days simulation
    t0_sim = time.perf_counter()
    events = kernel.run_simulation(ticks=sim_ticks)
    t1_sim = time.perf_counter()

    sim_time_sec = t1_sim - t0_sim
    num_events = len(events)
    events_per_sec = num_events / sim_time_sec if sim_time_sec > 0 else 0

    print(f"[Phase 4: Simulation Execution] Executed {sim_ticks} Ticks in {sim_time_sec:.3f} s")
    print(f"  - Total Causal Events Generated: {num_events:,}")
    print(f"  - SIMULATION KERNEL THROUGHPUT: {events_per_sec:,.0f} Events / Sec")

    # STEP 6: Subsystem 5 Database Materialization Benchmarking
    t0_mat = time.perf_counter()
    SQLiteMaterializer().materialize(kernel.state_store.get_all(), events, conn)
    t1_mat = time.perf_counter()

    mat_time_sec = t1_mat - t0_mat
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    populated_tables = cursor.fetchone()[0]

    total_rows = 0
    for tname in sdm.tables.keys():
        cursor.execute(f"SELECT count(*) FROM \"{tname}\";")
        total_rows += cursor.fetchone()[0]

    rows_per_sec = total_rows / mat_time_sec if mat_time_sec > 0 else 0

    print(f"[Phase 5: Materialization] Populated {total_rows:,} rows across {populated_tables} DB tables in {mat_time_sec:.3f} s")
    print(f"  - MATERIALIZATION THROUGHPUT: {rows_per_sec:,.0f} Rows / Sec")

    # STEP 7: Benchmark Summary & Verification
    print("\n==========================================================================")
    print(" CHRONOS ENGINE 50+ TABLE BENCHMARK SUMMARY")
    print("==========================================================================")
    print(f"  * Total Tables Introspected: {num_tables}")
    print(f"  * Total Foreign Key Constraints: {total_fks}")
    print(f"  * Total Introspection + Compilation Latency: {(t1_comp - t0_intro)*1000:.2f} ms")
    print(f"  * Simulation Kernel Engine Speed: {events_per_sec:,.0f} Events/sec")
    print(f"  * Target DB Population Speed: {rows_per_sec:,.0f} Rows/sec")
    print("==========================================================================")

    conn.close()

if __name__ == "__main__":
    run_50_table_stress_test()
