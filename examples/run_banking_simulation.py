"""
Enterprise Banking & Financial Services Simulation Runner for Chronos Engine.
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

def run_banking_domain():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banking_enterprise.db")
    
    if os.path.exists(db_file):
        os.remove(db_file)

    print("==========================================================================")
    print(" CHRONOS SIMULATION ENGINE: ENTERPRISE BANKING & FINANCIAL SERVICES DOMAIN")
    print("==========================================================================")

    # 1. Bootstrap Banking Database Schema
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE TB_BRANCH (
        branch_id TEXT PRIMARY KEY,
        city TEXT NOT NULL,
        cash_reserve REAL
    );

    CREATE TABLE TB_CUSTOMER (
        customer_id TEXT PRIMARY KEY,
        branch_id TEXT REFERENCES TB_BRANCH(branch_id),
        credit_score INTEGER,
        income REAL,
        account_balance REAL,
        loan_approved INTEGER,
        risk_status TEXT
    );

    CREATE TABLE TB_ACCOUNT (
        account_id TEXT PRIMARY KEY,
        customer_id TEXT REFERENCES TB_CUSTOMER(customer_id),
        account_type TEXT,
        balance REAL
    );

    CREATE TABLE TB_LOAN_APPLICATION (
        loan_id TEXT PRIMARY KEY,
        customer_id TEXT REFERENCES TB_CUSTOMER(customer_id),
        requested_amount REAL,
        status TEXT
    );

    CREATE TABLE TB_TRANSACTION_LOG (
        txn_id TEXT PRIMARY KEY,
        account_id TEXT REFERENCES TB_ACCOUNT(account_id),
        amount REAL,
        txn_type TEXT,
        timestamp TEXT
    );
    """)
    conn.commit()
    print(f"[Phase 1] Created Banking Database Schema at: {db_file}")

    # 2. Introspect Schema
    print("[Phase 2] Introspecting Banking Schema via SQLite Connection...")
    introspector = SQLiteIntrospector(domain_name="Banking_Domain")
    sdm = introspector.inspect(conn)
    print(f"  - Introspected {len(sdm.tables)} tables into Structural Domain Model.")

    # 3. Enrich & Compile
    print("[Phase 3] Compiling Chronos IR Plan for Banking Engine...")
    enricher = SemanticEnrichmentEngine()
    bdm = enricher.enrich(sdm)
    compiler = ChronosCompiler(root_seed=77777)
    ir = compiler.compile(bdm)

    # 4. Execute Simulation Kernel
    print("[Phase 4] Launching Discrete Event Simulation Kernel for 60 Days...")
    kernel = SimulationKernel(ir)
    kernel.bootstrap_world({"TB_BRANCH": 1, "TB_CUSTOMER": 8})
    events = kernel.run_simulation(ticks=60)
    print(f"  - Simulation Completed ({len(events)} transaction events logged).")

    # 5. Populate Live Database
    print("\n[Phase 5] Materializing simulated banking data into SQLite database...")
    SQLiteMaterializer().materialize(kernel.state_store.get_all(), events, conn)

    # 6. Execute SQL Queries to Verify Materialized Banking State
    print("\n==========================================================================")
    print(" 1. MATERIALIZED BANKING CUSTOMERS & RISK PROFILES (TB_CUSTOMER)")
    print("==========================================================================")
    cursor.execute("""
    SELECT customer_id, credit_score, income, account_balance, risk_status, loan_approved
    FROM TB_CUSTOMER
    ORDER BY credit_score DESC;
    """)
    rows = cursor.fetchall()
    print(f"{'Customer ID':<15} | {'Credit Score':<12} | {'Income':<12} | {'Balance':<12} | {'Risk Status':<12} | {'Loan Approved'}")
    print("-" * 85)
    for r in rows:
        cid, score, inc, bal, risk, loan = r
        loan_str = "APPROVED" if loan == 1 or loan == True else "REJECTED"
        inc_val = float(inc) if inc is not None else 0.0
        bal_val = float(bal) if bal is not None else 0.0
        score_val = int(score) if score is not None else 0
        print(f"{str(cid):<15} | {score_val:<12} | ${inc_val:<11.2f} | ${bal_val:<11.2f} | {str(risk):<12} | {loan_str}")

    print("\n==========================================================================")
    print(" 2. LOAN EVALUATION DECISIONS (TB_LOAN_APPLICATION)")
    print("==========================================================================")
    cursor.execute("""
    SELECT loan_id, customer_id, requested_amount, status
    FROM TB_LOAN_APPLICATION;
    """)
    rows = cursor.fetchall()
    print(f"{'Loan ID':<25} | {'Customer ID':<15} | {'Requested Amount':<18} | {'Status'}")
    print("-" * 75)
    for r in rows:
        lid, cid, amt, st = r
        amt_val = float(amt) if amt is not None else 0.0
        print(f"{str(lid):<25} | {str(cid):<15} | ${amt_val:<17.2f} | {str(st)}")

    print("\n==========================================================================")
    print(" 3. SAMPLE BANKING TRANSACTIONS (TB_TRANSACTION_LOG)")
    print("==========================================================================")
    cursor.execute("""
    SELECT txn_id, account_id, txn_type, amount, timestamp
    FROM TB_TRANSACTION_LOG
    LIMIT 8;
    """)
    rows = cursor.fetchall()
    print(f"{'Txn ID':<25} | {'Account ID':<15} | {'Type':<10} | {'Amount':<10} | {'Timestamp'}")
    print("-" * 75)
    for r in rows:
        amt_val = float(r[3]) if r[3] is not None else 0.0
        print(f"{str(r[0]):<25} | {str(r[1]):<15} | {str(r[2]):<10} | ${amt_val:<9.2f} | {str(r[4])}")
    print("==========================================================================")

    conn.close()

if __name__ == "__main__":
    run_banking_domain()
