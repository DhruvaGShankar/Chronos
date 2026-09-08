"""
Safe Rule & Policy Invariant Expression Evaluator.
"""

from typing import Dict, Any

class ExpressionEvaluator:
    """Evaluates rule conditions and state transitions against entity attributes safely."""

    @staticmethod
    def evaluate_condition(expr: str, context: Dict[str, Any]) -> bool:
        """Evaluates condition string safely within entity context."""
        try:
            return bool(eval(expr, {"__builtins__": {}}, context))
        except Exception:
            return False
