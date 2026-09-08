"""
Domain-Agnostic Declarative Discrete-Event Simulation Runtime Kernel.
Executes compiled Chronos IR bytecode plans deterministically across any arbitrary enterprise domain without hardcoded Python domain handlers.
"""

import uuid
from typing import Dict, List, Any
from chronos.core.types import ChronosIR, CausalEvent
from chronos.core.prng import PRNGSeedTree
from chronos.runtime.state_store import EntityStateStore
from chronos.runtime.executor import ExpressionEvaluator
from chronos.runtime.declarative_engine import DeclarativeIRExecutor

class SimulationKernel:
    """Universal domain-agnostic discrete-event simulation engine executing pure Chronos IR bytecode."""

    def __init__(self, ir: ChronosIR):
        self.ir = ir
        self.clock: int = 0
        self.seed_tree = PRNGSeedTree(ir.seed_root)
        self.state_store = EntityStateStore()
        self.causal_event_log: List[CausalEvent] = []

    def bootstrap_world(self, entity_counts: Dict[str, int]):
        """Populates baseline entity instances in topological creation order from IR specification."""
        for entity_name in self.ir.execution_topology:
            # Skip dynamic log tables specified in IR schedules
            log_tables = [s.get("log_target_entity") for s in self.ir.schedules if s.get("log_target_entity")]
            if entity_name in log_tables:
                continue

            count = entity_counts.get(entity_name, 5)
            entity_def = self.ir.entities.get(entity_name, {})
            cols = entity_def.get("columns", {})

            for i in range(count):
                entity_seed = self.seed_tree.derive_entity_seed(entity_name, i + 1)
                prng = self.seed_tree.get_prng(entity_seed)
                ent_id = f"{entity_name.lower()}_{i+1:03d}"

                record: Dict[str, Any] = {
                    "id": ent_id,
                    "type": entity_name,
                    "created_tick": 0
                }

                # Generic Column Initialization from Schema Definition
                for col_name, c_type in cols.items():
                    if col_name == f"{entity_name.lower()}_id" or col_name == "id":
                        record[col_name] = ent_id
                    elif col_name.endswith("_id"):
                        ref_type = col_name.replace("_id", "")
                        record[col_name] = f"tb_{ref_type}_001"
                    elif col_name == "name" or col_name.endswith("_name") or col_name.endswith("_code"):
                        record[col_name] = f"{entity_name}_{col_name}_{i+1}"
                    elif c_type in ["FLOAT", "INTEGER"]:
                        record[col_name] = round(prng.uniform(10.0, 500.0), 2)
                    elif c_type == "STRING":
                        record[col_name] = f"{col_name}_val_{i+1}"

                # Ensure primary key uniqueness
                pk_candidates = [c for c in cols.keys() if c.endswith("_id")]
                if pk_candidates:
                    primary_pk = pk_candidates[0]
                    for candidate in pk_candidates:
                        if candidate.replace("_id", "") in entity_name.lower():
                            primary_pk = candidate
                            break
                    record[primary_pk] = ent_id

                # Persona vectors assigned to ACTOR entities
                if "persona_vector" in entity_def and entity_def["persona_vector"]:
                    for trait in entity_def["persona_vector"]:
                        record[trait] = round(prng.uniform(0.15, 0.98), 2)

                self.state_store.add_entity(entity_name, record)

    def run_simulation(self, ticks: int = 90) -> List[CausalEvent]:
        """Executes timeline ticks strictly by evaluating declarative IR schedules and rules."""
        for tick in range(1, ticks + 1):
            self.clock = tick

            # 1. Execute Declarative IR Event Schedules
            for sched in self.ir.schedules:
                DeclarativeIRExecutor.execute_schedule_entry(
                    schedule_def=sched,
                    state_store=self.state_store,
                    seed_tree=self.seed_tree,
                    tick=tick,
                    causal_event_log=self.causal_event_log
                )

            # 2. Evaluate Declarative IR Invariants & Policy Rules
            self._evaluate_declarative_rules(tick)

        return self.causal_event_log

    def _evaluate_declarative_rules(self, tick: int):
        """Evaluates invariant rules and applies violation actions dynamically from IR."""
        for rule in self.ir.rules:
            target_entity = rule.get("target")
            expr = rule.get("invariant")
            action = rule.get("action")

            if not target_entity or not expr:
                continue

            for entity in self.state_store.get_entities(target_entity):
                passes_invariant = ExpressionEvaluator.evaluate_condition(expr, entity)
                
                # If rule specifies action string like "SET placement_eligible = True"
                if action and action.startswith("SET "):
                    mutation_str = action.replace("SET ", "")
                    if "=" in mutation_str:
                        attr, val_expr = mutation_str.split("=", 1)
                        attr = attr.strip()
                        val_expr = val_expr.strip()

                        if passes_invariant:
                            if val_expr.upper() == "TRUE":
                                entity[attr] = 1 if isinstance(entity.get(attr), int) else True
                            elif val_expr.upper() == "FALSE":
                                entity[attr] = 0 if isinstance(entity.get(attr), int) else False
                            else:
                                entity[attr] = val_expr.strip("'\"")
                        else:
                            if val_expr.upper() == "TRUE":
                                entity[attr] = 0 if isinstance(entity.get(attr), int) else False
                            elif val_expr.upper() == "FALSE":
                                entity[attr] = 1 if isinstance(entity.get(attr), int) else True
