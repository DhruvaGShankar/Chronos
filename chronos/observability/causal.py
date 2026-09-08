"""
Diagnostic Root-Cause Causal Explainer Engine.
Traces entity state transitions backward through event cause-ids to explain why an entity entered a specific state.
"""

from typing import List, Dict, Any, Optional
from chronos.core.types import CausalEvent

class CausalExplainerEngine:
    """Extracts step-by-step causal explanation chains for entity attribute state transitions."""

    @staticmethod
    def explain_entity_state(
        event_log: List[CausalEvent],
        actor_id: str
    ) -> List[Dict[str, Any]]:
        """Extracts the chronological sequence of causal events involving the specified actor_id."""
        history = []
        for e in event_log:
            if e.actor_id == actor_id or (isinstance(e.payload, dict) and e.payload.get("actor_id") == actor_id):
                history.append({
                    "event_id": e.event_id,
                    "tick": e.tick,
                    "event_type": e.event_type,
                    "target": e.target_id,
                    "payload": e.payload
                })
        return history

    @staticmethod
    def format_explanation_report(actor_id: str, history: List[Dict[str, Any]]) -> str:
        """Formats the causal explanation history into a human-readable diagnostic report."""
        lines = []
        lines.append("========================================================================")
        lines.append(f" CAUSAL DIAGNOSTIC EXPLANATION REPORT: Entity '{actor_id}'")
        lines.append("========================================================================")

        if not history:
            lines.append(f" No causal events recorded for entity '{actor_id}'.")
        else:
            for item in history:
                lines.append(f" [Tick {item['tick']:02d}] Event: {item['event_type']:<30} Target: {item['target']}")
                lines.append(f"             Details: {item['payload']}")

        lines.append("========================================================================")
        return "\n".join(lines)
