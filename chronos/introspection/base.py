"""
Base Introspector Abstract Interface.
"""

from abc import ABC, abstractmethod
from typing import Any
from chronos.core.types import StructuralDomainModel

class BaseIntrospector(ABC):
    """Abstract Base Class for all Chronos schema introspectors (PostgreSQL, SQLite, SQL DDL)."""

    def __init__(self, domain_name: str = "EnterpriseDomain"):
        self.domain_name = domain_name

    @abstractmethod
    def inspect(self, source: Any) -> StructuralDomainModel:
        """Parses raw source schema metadata into a standardized StructuralDomainModel (SDM)."""
        pass
