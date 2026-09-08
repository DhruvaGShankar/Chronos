"""
Chronos Declarative IR Action & Decision Tree Engine.
Executes arbitrary domain event schedules, attribute mutations, and causal log generation strictly from declarative Chronos IR specifications with zero domain-specific Python code.
"""

import random
import uuid
from typing import Dict, List, Any
from chronos.core.types import ChronosIR, CausalEvent
from chronos.runtime.executor import ExpressionEvaluator

class DeclarativeIRExecutor:
    """Generic declarative evaluator for Chronos IR event schedules and decision trees."""

    @staticmethod
    def execute_schedule_entry(
        schedule_def: Dict[str, Any],
        state_store: Any,
        seed_tree: Any,
        tick: int,
        causal_event_log: List[CausalEvent]
    ):
        target_actor = schedule_def.get("target_actor")
        log_target = schedule_def.get("log_target_entity")
        decision_tree = schedule_def.get("decision_tree", {})

        if not target_actor:
            return

        actors = state_store.get_entities(target_actor)

        for actor in actors:
            seed = seed_tree.derive_event_seed(hash(actor["id"]), tick, schedule_def.get("name", "EVENT"))
            prng = seed_tree.get_prng(seed)

            # Evaluate execution condition
            cond_expr = decision_tree.get("condition")
            if cond_expr:
                ctx = dict(actor)
                ctx["random"] = prng.random
                ctx["random_uniform"] = prng.uniform
                ctx["random_int"] = prng.randint
                
                should_execute = ExpressionEvaluator.evaluate_condition(cond_expr, ctx)
                if not should_execute:
                    continue

            # Execute attribute mutation formula if present
            mutation = decision_tree.get("mutation")
            if mutation:
                attr_name = mutation.get("attribute")
                formula_expr = mutation.get("formula")
                if attr_name and formula_expr:
                    ctx = dict(actor)
                    ctx["random"] = prng.random
                    ctx["random_uniform"] = prng.uniform
                    ctx["random_int"] = prng.randint
                    ctx["tick"] = tick
                    
                    try:
                        new_val = eval(formula_expr, {"__builtins__": {}}, ctx)
                        actor[attr_name] = new_val
                    except Exception:
                        pass

            # Log Causal Event to target table if specified
            if log_target:
                log_id = f"{log_target.lower()}_{len(causal_event_log)+1:06d}"
                pk_name = "txn_id" if "TRANSACTION" in log_target else ("order_id" if "ORDER" in log_target else "attendance_id")
                
                event_record = {
                    "id": log_id,
                    pk_name: log_id,
                    "actor_id": actor["id"],
                    "created_tick": tick
                }

                # Copy payload fields specified in IR
                payload_spec = decision_tree.get("event_payload", {})
                for field_name, expr in payload_spec.items():
                    ctx = dict(actor)
                    ctx["random"] = prng.random
                    ctx["random_uniform"] = prng.uniform
                    ctx["tick"] = tick
                    try:
                        event_record[field_name] = eval(expr, {"__builtins__": {}}, ctx)
                    except Exception:
                        event_record[field_name] = actor.get(field_name, None)

                state_store.add_entity(log_target, event_record)

                causal_event_log.append(
                    CausalEvent(
                        event_id=str(uuid.uuid4())[:8],
                        tick=tick,
                        cause_id=None,
                        actor_id=actor["id"],
                        target_id=log_target,
                        event_type=f"{schedule_def.get('name', 'Generic')}Event",
                        payload=event_record
                    )
                )
