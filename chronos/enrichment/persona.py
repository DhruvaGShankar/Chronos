"""
Persona Matrix & Behavioral Trait Distribution Module.
"""

from typing import List, Dict
from chronos.core.types import PersonaProfile, EntityRole, StructuralDomainModel

class PersonaMatrixBuilder:
    """Binds persona trait profiles to ACTOR entities in the domain model."""

    @staticmethod
    def build_default_personas(sdm: StructuralDomainModel) -> Dict[str, PersonaProfile]:
        personas: Dict[str, PersonaProfile] = {}

        for table_name, tdef in sdm.tables.items():
            if tdef.inferred_role == EntityRole.ACTOR:
                personas[table_name] = PersonaProfile(
                    entity_name=table_name,
                    vector_attributes=["conscientiousness", "aptitude", "financial_stability"],
                    base_distributions={
                        "conscientiousness": {"mean": 0.55, "std": 0.20},
                        "aptitude": {"mean": 0.60, "std": 0.18},
                        "financial_stability": {"mean": 0.65, "std": 0.22}
                    }
                )

        return personas
