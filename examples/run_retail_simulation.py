"""
Enterprise Retail & E-Commerce Supply Chain Simulation Runner for Chronos Engine.
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

def run_retail_domain():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retail_enterprise.db")
    
    if os.path.exists(db_file):
        os.remove(db_file)

    print("==========================================================================")
    print(" CHRONOS SIMULATION ENGINE: RETAIL & E-COMMERCE SUPPLY CHAIN DOMAIN")
    print("==========================================================================")

    # 1. Bootstrap Retail Database Schema
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE TB_STORE (
        store_id TEXT PRIMARY KEY,
        location TEXT NOT NULL,
        region TEXT NOT NULL
    );

    CREATE TABLE TB_PRODUCT (
        product_id TEXT PRIMARY KEY,
        product_code TEXT NOT NULL,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock_level INTEGER
    );

    CREATE TABLE TB_SHOPPER (
        shopper_id TEXT PRIMARY KEY,
        store_id TEXT REFERENCES TB_STORE(store_id),
        disposable_income REAL,
        impulse_buy_index REAL,
        total_spent REAL,
        vip_status INTEGER
    );

    CREATE TABLE TB_ORDER (
        order_id TEXT PRIMARY KEY,
        shopper_id TEXT REFERENCES TB_SHOPPER(shopper_id),
        order_date TEXT,
        total_amount REAL,
        status TEXT
    );
    """)
    conn.commit()
    print(f"[Phase 1] Created Retail Database Schema at: {db_file}")

    # 2. Introspect Schema
    print("[Phase 2] Introspecting Retail Schema via SQLite Connection...")
    introspector = SQLiteIntrospector(domain_name="Retail_Domain")
    sdm = introspector.inspect(conn)
    print(f"  - Introspected {len(sdm.tables)} tables into Structural Domain Model.")

    # 3. Enrich & Compile
    print("[Phase 3] Compiling Chronos IR Plan for Retail Engine...")
    enricher = SemanticEnrichmentEngine()
    bdm = enricher.enrich(sdm)
    compiler = ChronosCompiler(root_seed=88888)
    ir = compiler.compile(bdm)

    # 4. Execute Simulation Kernel
    print("[Phase 4] Launching Discrete Event Simulation Kernel for 60 Days...")
    kernel = SimulationKernel(ir)
    kernel.bootstrap_world({"TB_STORE": 1, "TB_SHOPPER": 8})
    events = kernel.run_simulation(ticks=60)
    print(f"  - Simulation Completed ({len(events)} customer purchase orders logged).")

    # 5. Materialize into Live Database
    print("\n[Phase 5] Materializing simulated retail data into SQLite database...")
    SQLiteMaterializer().materialize(kernel.state_store.get_all(), events, conn)

    # 6. Execute SQL Queries to Verify Materialized State
    print("\n==========================================================================")
    print(" 1. MATERIALIZED SHOPPERS & VIP CLASSIFICATIONS (TB_SHOPPER)")
    print("==========================================================================")
    cursor.execute("""
    SELECT shopper_id, disposable_income, impulse_buy_index, total_spent, vip_status
    FROM TB_SHOPPER
    ORDER BY total_spent DESC;
    """)
    rows = cursor.fetchall()
    print(f"{'Shopper ID':<15} | {'Disp. Income':<14} | {'Impulse Index':<15} | {'Total Spent':<14} | {'VIP Status'}")
    print("-" * 78)
    for r in rows:
        sid, inc, impulse, spent, vip = r
        vip_str = "VIP MEMBER" if vip == 1 else "STANDARD"
        print(f"{sid:<15} | ${inc:<13.2f} | {impulse:<15.2f} | ${spent:<13.2f} | {vip_str}")

    print("\n==========================================================================")
    print(" 2. MATERIALIZED PRODUCT CATALOG (TB_PRODUCT)")
    print("==========================================================================")
    cursor.execute("""
    SELECT product_code, product_name, category, price, stock_level
    FROM TB_PRODUCT;
    """)
    rows = cursor.fetchall()
    print(f"{'Code':<10} | {'Product Name':<25} | {'Category':<15} | {'Price':<8} | {'Stock'}")
    print("-" * 72)
    for r in rows:
        print(f"{r[0]:<10} | {r[1]:<25} | {r[2]:<15} | ${r[3]:<7.2f} | {r[4]}")

    print("\n==========================================================================")
    print(" 3. SAMPLE PURCHASE ORDERS (TB_ORDER)")
    print("==========================================================================")
    cursor.execute("""
    SELECT order_id, shopper_id, total_amount, order_date, status
    FROM TB_ORDER
    LIMIT 8;
    """)
    rows = cursor.fetchall()
    print(f"{'Order ID':<12} | {'Shopper ID':<15} | {'Amount':<10} | {'Order Date':<12} | {'Status'}")
    print("-" * 65)
    for r in rows:
        print(f"{r[0]:<12} | {r[1]:<15} | ${r[2]:<9.2f} | {r[3]:<12} | {r[4]}")
    print("==========================================================================")

    conn.close()

if __name__ == "__main__":
    run_retail_domain()
