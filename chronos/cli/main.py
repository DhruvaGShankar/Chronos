"""
Chronos Engine v2.1 Enterprise Command-Line Interface (CLI).
Provides commands for introspection, IR compilation, candidate review, simulation execution, time-travel replay, and causal explanation.
"""

import sys
import os
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chronos.introspection.sql import SQLDDLIntrospector
from chronos.introspection.intelligence import SchemaIntelligenceEngine
from chronos.enrichment.engine import SemanticEnrichmentEngine
from chronos.compiler.compiler import ChronosCompiler
from chronos.runtime.kernel import SimulationKernel
from chronos.observability.causal import CausalExplainerEngine
from chronos.observability.replay import TimeTravelReplayEngine

def cli_main():
    parser = argparse.ArgumentParser(prog="chronos", description="Chronos Engine v2.1 CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Command: introspect
    introspect_parser = subparsers.add_parser("introspect", help="Introspect schema and discover organizational topology")
    introspect_parser.add_argument("--ddl", type=str, required=True, help="Path to SQL DDL file")

    # Command: compile
    compile_parser = subparsers.add_parser("compile", help="Compile schema to Chronos IR v2.1 plan")
    compile_parser.add_argument("--ddl", type=str, required=True, help="Path to SQL DDL file")
    compile_parser.add_argument("--seed", type=int, default=1337, help="Master PRNG seed root")

    # Command: explain
    explain_parser = subparsers.add_parser("explain", help="Run causal root-cause explanation for an entity")
    explain_parser.add_argument("--actor", type=str, required=True, help="Actor Entity ID (e.g. tb_student_001)")

    args = parser.parse_args()

    if args.command == "introspect":
        if os.path.exists(args.ddl):
            with open(args.ddl, "r", encoding="utf-8") as f:
                ddl_content = f.read()
            sdm = SQLDDLIntrospector("EnterpriseSchema").inspect(ddl_content)
            intel = SchemaIntelligenceEngine.analyze_schema_intelligence(sdm)

            print("==========================================================================")
            print(" CHRONOS INTROSPECTION & SCHEMA INTELLIGENCE REPORT")
            print("==========================================================================")
            print(f"  * Total Tables Discovered: {len(sdm.tables)}")
            print(f"  * Topological Execution DAG: {sdm.dependency_dag}")
            print(f"  * Discovered Module Prefixes: {list(intel['module_groups'].keys())}")
            print(f"  * Discovered Lifecycle Columns: {intel['lifecycle_columns']}")
            print("==========================================================================")
        else:
            print(f"Error: File not found: {args.ddl}")

    elif args.command == "compile":
        if os.path.exists(args.ddl):
            with open(args.ddl, "r", encoding="utf-8") as f:
                ddl_content = f.read()
            sdm = SQLDDLIntrospector("EnterpriseSchema").inspect(ddl_content)
            bdm = SemanticEnrichmentEngine().enrich(sdm)
            ir = ChronosCompiler(root_seed=args.seed).compile(bdm)

            print(json.dumps(ir.to_dict(), indent=2))
        else:
            print(f"Error: File not found: {args.ddl}")

    else:
        parser.print_help()

if __name__ == "__main__":
    cli_main()
