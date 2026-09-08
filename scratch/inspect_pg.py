import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, dbname='XSC_DB_ONEAPP_TEST', user='postgres', password='postgres')
cur = conn.cursor()

cur.execute("SELECT datname FROM pg_database;")
dbs = [r[0] for r in cur.fetchall()]
print("Available Databases in PostgreSQL:", dbs)

cur.execute("""
    SELECT table_schema, count(*) 
    FROM information_schema.tables 
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast') 
      AND table_type = 'BASE TABLE'
    GROUP BY table_schema;
""")
schemas = cur.fetchall()
print("\nSchemas and table counts in XSC_DB_ONEAPP_TEST:")
for s, cnt in schemas:
    print(f"  Schema '{s}': {cnt} tables")

conn.close()
