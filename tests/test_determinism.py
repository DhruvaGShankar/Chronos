"""
Unit Tests for Bit-Exact Simulation Determinism.
"""

from chronos.introspection.sql_ddl import SQLDDLIntrospector
from chronos.enrichment.engine import SemanticEnrichmentEngine
from chronos.compiler.compiler import ChronosCompiler
from chronos.runtime.kernel import SimulationKernel

def test_bit_exact_determinism():
    sql = """
    CREATE TABLE TB_DEPT (dept_id VARCHAR(36) PRIMARY KEY);
    CREATE TABLE TB_STUDENT (student_id VARCHAR(36) PRIMARY KEY, cgpa FLOAT, attendance_pct FLOAT, fee_status VARCHAR(20));
    CREATE TABLE TB_ATTENDANCE (attendance_id VARCHAR(36) PRIMARY KEY, timestamp DATETIME);
    """

    def run_sim(seed):
        sdm = SQLDDLIntrospector("Test").inspect(sql)
        bdm = SemanticEnrichmentEngine().enrich(sdm)
        ir = ChronosCompiler(root_seed=seed).compile(bdm)
        kernel = SimulationKernel(ir)
        kernel.bootstrap_world({"TB_DEPT": 1, "TB_STUDENT": 5})
        kernel.run_simulation(ticks=30)
        return kernel.state_store.get_entities("TB_STUDENT")

    run1 = run_sim(seed=9999)
    run2 = run_sim(seed=9999)

    assert len(run1) == len(run2)
    for s1, s2 in zip(run1, run2):
        assert s1["id"] == s2["id"]
        assert s1["conscientiousness"] == s2["conscientiousness"]
        assert s1["cgpa"] == s2["cgpa"]
        assert s1["attendance_pct"] == s2["attendance_pct"]

if __name__ == "__main__":
    test_bit_exact_determinism()
    print("test_bit_exact_determinism PASSED.")
