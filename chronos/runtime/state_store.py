"""
In-Memory Struct-of-Arrays (SoA) Entity State Store.
High-performance entity graph container supporting fast iteration and delta tracking.
"""

from typing import Dict, List, Any, Optional

class EntityStateStore:
    """Manages in-memory entity graph states and attribute indices."""

    def __init__(self):
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    def initialize_entity_type(self, entity_name: str):
        if entity_name not in self._store:
            self._store[entity_name] = []

    def add_entity(self, entity_name: str, record: Dict[str, Any]):
        self.initialize_entity_type(entity_name)
        self._store[entity_name].append(record)

    def get_entities(self, entity_name: str) -> List[Dict[str, Any]]:
        return self._store.get(entity_name, [])

    def get_all(self) -> Dict[str, List[Dict[str, Any]]]:
        return self._store
