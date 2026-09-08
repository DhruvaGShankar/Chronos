import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, dbname='XSC_DB_ONEAPP_SIM', user='postgres', password='postgres')
cur = conn.cursor()

cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
      AND table_type = 'BASE TABLE';
""")
tables = cur.fetchall()

populated = []
for s, t in tables:
    full_t = f'"{s}"."{t}"'
    try:
        cur.execute(f'SELECT count(*) FROM {full_t};')
        cnt = cur.fetchone()[0]
        if cnt > 0:
            populated.append((f"{s}.{t}", cnt))
    except Exception:
        conn.rollback()

print(f"=== TARGET DATABASE (XSC_DB_ONEAPP_SIM) POPULATION ===")
print(f"Total Populated Tables: {len(populated)}")
for t, cnt in populated:
    print(f"  - {t:<45} : {cnt} rows")

conn.close()
