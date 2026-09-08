"""
Time-Travel Simulation State Replay Engine.
Reconstructs exact entity states at any historical timeline tick from recorded causal event envelopes.
"""

from typing import Dict, List, Any, Optional
from chronos.core.types import CausalEvent
from chronos.core.exceptions import ReplayExecutionError

class TimeTravelReplayEngine:
    """Reconstructs point-in-time state snapshots by replaying causal event logs."""

    @staticmethod
    def replay_state_at_tick(
        event_log: List[CausalEvent],
        initial_snapshots: Dict[str, List[Dict[str, Any]]],
        target_tick: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Reconstructs world state at target_tick by replaying event log transitions up to target_tick."""
        if target_tick < 0:
            raise ReplayExecutionError(f"Invalid target tick: {target_tick}")

        # Deep copy initial tick 0 state
        reconstructed_state: Dict[str, List[Dict[str, Any]]] = {}
        for tname, records in initial_snapshots.items():
            reconstructed_state[tname] = [dict(r) for r in records]

        # Replay event log entries up to target_tick
        for event in event_log:
            if event.tick > target_tick:
                break

            target_table = event.target_id
            payload = event.payload

            if target_table in reconstructed_state:
                # Find matching record if update, or append if new entity
                entity_id = payload.get("id") or payload.get(f"{target_table.lower()}_id")
                found = False

                for r in reconstructed_state[target_table]:
                    if r.get("id") == entity_id or r.get(f"{target_table.lower()}_id") == entity_id:
                        r.update(payload)
                        found = True
                        break

                if not found:
                    reconstructed_state[target_table].append(dict(payload))
            else:
                reconstructed_state[target_table] = [dict(payload)]

        return reconstructed_state
