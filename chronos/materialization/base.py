"""
Abstract Base Class for Output Materializers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from chronos.core.types import CausalEvent

class BaseMaterializer(ABC):
    """Abstract base class for output target materializers."""

    @abstractmethod
    def materialize(self, entity_store: Dict[str, List[Dict[str, Any]]], event_log: List[CausalEvent], target_path: str):
        """Materializes simulated state to the target destination."""
        pass
