"""
Chronos Schema Intelligence Layer.
Performs structural inference on database schemas to discover entity roles, aggregate boundaries, module prefixes, lifecycle state columns, temporal tracking, audit patterns, and junction tables.
"""

from typing import Dict, List, Any
from chronos.core.types import StructuralDomainModel, TableDef

class SchemaIntelligenceEngine:
    """Discovers structural organization, lifecycle columns, and aggregate boundaries."""

    @staticmethod
    def analyze_schema_intelligence(sdm: StructuralDomainModel) -> Dict[str, Any]:
        """Analyzes structural domain model to produce a Schema Intelligence Report."""
        module_groups: Dict[str, List[str]] = {}
        lifecycle_columns: Dict[str, List[str]] = {}
        temporal_columns: Dict[str, List[str]] = {}
        audit_patterns: Dict[str, List[str]] = {}
        junction_tables: List[str] = []

        for tname, tdef in sdm.tables.items():
            cols = [c.lower() for c in tdef.columns.keys()]

            # 1. Module & Prefix Grouping (e.g. TB_USER_*, TB_FINANCE_*)
            parts = tname.split("_")
            prefix = parts[0] if len(parts) < 2 else f"{parts[0]}_{parts[1]}"
            if prefix not in module_groups:
                module_groups[prefix] = []
            module_groups[prefix].append(tname)

            # 2. Lifecycle & State Status Column Detection
            states = [c for c in cols if any(k in c for k in ["status", "state", "stage", "flag", "phase"])]
            if states:
                lifecycle_columns[tname] = states

            # 3. Temporal Tracking Column Detection
            times = [c for c in cols if any(k in c for k in ["created", "updated", "timestamp", "date", "time", "tick"])]
            if times:
                temporal_columns[tname] = times

            # 4. Audit & Soft-Delete Column Detection
            audits = [c for c in cols if any(k in c for k in ["is_deleted", "deleted_at", "audit_id", "modified_by"])]
            if audits:
                audit_patterns[tname] = audits

            # 5. N:M Junction Table Detection (Table with 2+ Foreign Keys and few non-FK data columns)
            if len(tdef.foreign_keys) >= 2 and len(cols) <= (len(tdef.foreign_keys) + 3):
                junction_tables.append(tname)

        return {
            "module_groups": module_groups,
            "lifecycle_columns": lifecycle_columns,
            "temporal_columns": temporal_columns,
            "audit_patterns": audit_patterns,
            "junction_tables": junction_tables
        }
