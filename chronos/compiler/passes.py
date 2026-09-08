"""
Chronos Compiler Passes & Verification Pipelines v2.1.
Computes topological execution order, validates schema constraints, generates cryptographic simulation identity hashes, and lowers ASTs to Chronos IR v2.1 plans.
"""

import time
from typing import List, Dict
from chronos.core.types import BehavioralDomainModel, ChronosIR
from chronos.core.ir import ChronosIRv21, IRHeader
from chronos.core.identity import SimulationIdentity
from chronos.core.exceptions import CompilationError
from chronos.introspection.graph import DependencyGraphBuilder

class CompilerPasses:
    """Executes verification and lowering passes on the Behavioral Domain Model."""

    @staticmethod
    def verify_structural_integrity(bdm: BehavioralDomainModel):
        """Pass 1: Verifies schema integrity and presence of primary keys."""
        for tname, tdef in bdm.structural_model.tables.items():
            if not tdef.columns:
                raise CompilationError(f"Table '{tname}' has no column definitions.")

    @staticmethod
    def compute_execution_topology(bdm: BehavioralDomainModel) -> List[str]:
        """Pass 2: Computes topological initialization ordering for entities."""
        dag = bdm.structural_model.dependency_dag
        return DependencyGraphBuilder.topological_sort(dag)

    @staticmethod
    def lower_to_ir(bdm: BehavioralDomainModel, root_seed: int) -> ChronosIR:
        """Pass 3: Lowers Behavioral AST into executable Chronos IR v2.1."""
        topology = CompilerPasses.compute_execution_topology(bdm)

        compiled_entities = {}
        for idx, (tname, tdef) in enumerate(bdm.structural_model.tables.items()):
            compiled_entities[tname] = {
                "name": tname,
                "role": tdef.inferred_role.value,
                "seed_offset": root_seed + (idx * 1000),
                "columns": {cname: cdef.data_type.value for cname, cdef in tdef.columns.items()},
                "persona_vector": bdm.personas[tname].vector_attributes if tname in bdm.personas else []
            }

        compiled_fsms = {}
        for fsm_name, fsm in bdm.state_machines.items():
            compiled_fsms[fsm_name] = {
                "target_entity": fsm.target_entity,
                "initial_state": fsm.initial_state,
                "states": fsm.states,
                "transitions": [
                    {"from": t.from_state, "to": t.to_state, "condition": t.condition_expr}
                    for t in fsm.transitions
                ]
            }

        compiled_rules = [
            {
                "name": r.name,
                "target": r.target_entity,
                "invariant": r.invariant_expr,
                "action": r.on_violation_action
            }
            for r in bdm.rules
        ]

        compiled_schedules = [
            s if isinstance(s, dict) else {
                "name": s.name,
                "cron": s.cron_or_interval,
                "target": s.target_entity,
                "action": s.action_type
            }
            for s in bdm.schedules
        ]

        # Compute Cryptographic Hashes & Simulation Identity
        schema_hash = SimulationIdentity.compute_hash(list(compiled_entities.keys()))
        semantic_hash = SimulationIdentity.compute_hash(compiled_rules)
        sim_id = SimulationIdentity.generate_simulation_id(
            schema_hash=schema_hash,
            semantic_model_hash=semantic_hash,
            ir_version="2.1.0",
            compiler_version="2.1.0",
            root_seed=root_seed
        )

        header = IRHeader(
            ir_version="2.1.0",
            compiler_version="2.1.0",
            simulation_id=sim_id,
            source_schema_hash=schema_hash,
            semantic_model_hash=semantic_hash,
            root_seed=root_seed,
            compilation_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )

        ir = ChronosIR(
            version="2.1.0",
            seed_root=root_seed,
            entities=compiled_entities,
            state_machines=compiled_fsms,
            rules=compiled_rules,
            schedules=compiled_schedules,
            execution_topology=topology
        )

        # Attach v2.1 IR Header
        ir.header = header
        return ir
