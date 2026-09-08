"""
Foreign Key Dependency Graph & Topological Sort Analyzer.
"""

from typing import Dict, List, Set
from chronos.core.types import TableDef
from chronos.core.exceptions import CyclicDependencyError

class DependencyGraphBuilder:
    """Builds foreign-key dependency graphs and resolves topological creation ordering."""

    @staticmethod
    def build_dependency_dag(tables: Dict[str, TableDef]) -> Dict[str, List[str]]:
        """Constructs adjacency list representing parent-child dependency edges."""
        dag: Dict[str, List[str]] = {t: [] for t in tables.keys()}
        
        for tname, tdef in tables.items():
            for fk in tdef.foreign_keys:
                for col, ref in fk.items():
                    parent_table = ref.split('.')[0]
                    if parent_table in dag and tname not in dag[parent_table]:
                        dag[parent_table].append(tname)
                        
        return dag

    @staticmethod
    def topological_sort(dag: Dict[str, List[str]]) -> List[str]:
        """Performs topological sorting with cycle detection."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        order: List[str] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)

            for child in dag.get(node, []):
                if child not in visited:
                    dfs(child)
                elif child in rec_stack:
                    # Cyclic dependency detected
                    raise CyclicDependencyError(
                        f"Cyclic Foreign Key reference detected between '{node}' and '{child}'."
                    )

            rec_stack.remove(node)
            order.append(node)

        for node in list(dag.keys()):
            if node not in visited:
                dfs(node)

        return list(reversed(order))
