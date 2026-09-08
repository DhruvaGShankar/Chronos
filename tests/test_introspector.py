"""
Unit Tests for Schema Introspection Engine.
"""

from chronos.introspection.sql_ddl import SQLDDLIntrospector
from chronos.core.types import EntityRole

def test_sql_introspection():
    sql = """
    CREATE TABLE TB_COMPANY (
        company_id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(100)
    );

    CREATE TABLE TB_EMPLOYEE (
        emp_id VARCHAR(36) PRIMARY KEY,
        company_id VARCHAR(36) REFERENCES TB_COMPANY(company_id),
        name VARCHAR(100)
    );

    CREATE TABLE TB_TRANSACTION_LOG (
        log_id VARCHAR(36) PRIMARY KEY,
        emp_id VARCHAR(36) REFERENCES TB_EMPLOYEE(emp_id),
        timestamp DATETIME,
        amount FLOAT
    );
    """
    introspector = SQLDDLIntrospector(domain_name="Finance")
    sdm = introspector.inspect(sql)

    assert "TB_COMPANY" in sdm.tables
    assert "TB_EMPLOYEE" in sdm.tables
    assert "TB_TRANSACTION_LOG" in sdm.tables

    assert sdm.tables["TB_COMPANY"].inferred_role == EntityRole.ROOT
    assert sdm.tables["TB_EMPLOYEE"].inferred_role == EntityRole.ACTOR
    assert sdm.tables["TB_TRANSACTION_LOG"].inferred_role == EntityRole.EVENT_LOG

if __name__ == "__main__":
    test_sql_introspection()
    print("test_sql_introspection PASSED.")
