"""
Chronos IR v2.1 Intermediate Representation Specification.
Defines the strongly typed JSON plan header, execution plan, entity definitions, rules, and schedules.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class IRHeader:
    """Header metadata for Chronos IR v2.1 plans."""
    ir_version: str = "2.1.0"
    compiler_version: str = "2.1.0"
    simulation_id: str = ""
    source_schema_hash: str = ""
    semantic_model_hash: str = ""
    root_seed: int = 1337
    compilation_timestamp: str = ""

@dataclass
class ChronosIRv21:
    """Root Chronos IR v2.1 Executable Plan structure."""
    header: IRHeader
    execution_topology: List[str]
    entities: Dict[str, Any]
    state_machines: Dict[str, Any]
    rules: List[Dict[str, Any]]
    schedules: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes Chronos IR v2.1 plan to a standard JSON-compatible dictionary."""
        return {
            "ir_header": {
                "ir_version": self.header.ir_version,
                "compiler_version": self.header.compiler_version,
                "simulation_id": self.header.simulation_id,
                "hashes": {
                    "source_schema_hash": self.header.source_schema_hash,
                    "semantic_model_hash": self.header.semantic_model_hash
                },
                "root_seed": self.header.root_seed,
                "compilation_timestamp": self.header.compilation_timestamp
            },
            "execution_plan": {
                "execution_topology": self.execution_topology,
                "entities": self.entities,
                "state_machines": self.state_machines,
                "rules": self.rules,
                "schedules": self.schedules
            }
        }
