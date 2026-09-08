"""
Chronos Engine v2.1 Core Types & AST Node Specifications.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

class DataType(Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    JSON = "JSON"
    UUID = "UUID"

ColumnType = DataType

class EntityRole(Enum):
    ROOT = "ROOT"
    ACTOR = "ACTOR"
    EVENT_LOG = "EVENT_LOG"
    DIMENSION = "DIMENSION"

@dataclass
class ColumnDef:
    name: str
    data_type: DataType
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = None
    fk_ref_table: Optional[str] = None
    fk_ref_column: Optional[str] = None

@dataclass
class TableDef:
    name: str
    columns: Dict[str, ColumnDef] = field(default_factory=dict)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    inferred_role: EntityRole = EntityRole.DIMENSION

@dataclass
class StructuralDomainModel:
    domain_name: str
    tables: Dict[str, TableDef] = field(default_factory=dict)
    dependency_dag: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class PersonaProfile:
    entity_name: str
    vector_attributes: List[str]
    base_distributions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TransitionDef:
    from_state: str
    to_state: str
    condition_expr: str

StateTransition = TransitionDef

@dataclass
class FSMDef:
    name: str
    target_entity: str
    initial_state: str
    states: List[str]
    transitions: List[TransitionDef]

StateMachineDef = FSMDef

@dataclass
class RuleDef:
    name: str
    target_entity: str
    invariant_expr: str
    on_violation_action: str

@dataclass
class EventScheduleDef:
    name: str
    cron_or_interval: str
    target_entity: str
    action_type: str

@dataclass
class BehavioralDomainModel:
    structural_model: StructuralDomainModel
    personas: Dict[str, PersonaProfile] = field(default_factory=dict)
    state_machines: Dict[str, FSMDef] = field(default_factory=dict)
    rules: List[RuleDef] = field(default_factory=list)
    schedules: List[EventScheduleDef] = field(default_factory=list)

@dataclass
class ChronosIR:
    version: str
    seed_root: int
    entities: Dict[str, Any]
    state_machines: Dict[str, Any]
    rules: List[Dict[str, Any]]
    schedules: List[Dict[str, Any]]
    execution_topology: List[str]
    header: Optional[Any] = None

@dataclass
class CausalEvent:
    event_id: str
    tick: int
    cause_id: Optional[str]
    actor_id: str
    target_id: str
    event_type: str
    payload: Dict[str, Any]
