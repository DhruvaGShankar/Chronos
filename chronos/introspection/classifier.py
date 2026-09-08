"""
Rule-Based Entity Role Classifier.
Classifies database tables into ROOT, ACTOR, EVENT_LOG, or DIMENSION roles.
"""

from chronos.core.types import TableDef, EntityRole

class EntityClassifier:
    """Classifies entity roles using structural heuristics and column metadata."""

    @staticmethod
    def classify_role(table: TableDef) -> EntityRole:
        name_lower = table.name.lower()
        col_names = [c.lower() for c in table.columns.keys()]

        # Heuristic 1: High frequency timestamp logs -> EVENT_LOG
        has_timestamp = any("date" in c or "time" in c or "timestamp" in c for c in col_names)

        if ("log" in name_lower or "attendance" in name_lower or "transaction" in name_lower 
                or "submission" in name_lower or "result" in name_lower or "activity" in name_lower) and has_timestamp:
            return EntityRole.EVENT_LOG

        # Heuristic 2: Human/System Actors -> ACTOR
        if any(keyword in name_lower for keyword in ["student", "faculty", "employee", "user", "customer", "patient", "actor", "doctor"]):
            return EntityRole.ACTOR

        # Heuristic 3: Independent Container Entities (No Foreign Keys) -> ROOT
        if len(table.foreign_keys) == 0 and not has_timestamp:
            return EntityRole.ROOT

        # Default fallback -> DIMENSION
        return EntityRole.DIMENSION
