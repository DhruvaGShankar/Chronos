"""
Chronos Engine v2.1 Exception Hierarchy.
"""

class ChronosError(Exception):
    """Base exception for all Chronos engine errors."""
    pass

class SchemaIntrospectionError(ChronosError):
    """Raised when database introspection or DDL parsing fails."""
    pass

IntrospectionError = SchemaIntrospectionError

class CyclicDependencyError(SchemaIntrospectionError):
    """Raised when foreign key cycle dependencies are detected."""
    pass

class SemanticEnrichmentError(ChronosError):
    """Raised when semantic enrichment or policy binding fails."""
    pass

class CompilationError(ChronosError):
    """Raised when Chronos IR compilation or static verification passes fail."""
    pass

class SimulationRuntimeError(ChronosError):
    """Raised during simulation execution timeline failures."""
    pass

class ReplayExecutionError(ChronosError):
    """Raised during time-travel event replay failures."""
    pass

class ProjectionError(ChronosError):
    """Raised when state projection or database materialization fails."""
    pass
