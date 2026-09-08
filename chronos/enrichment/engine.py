"""
Master Semantic Enrichment Engine.
Combines Structural Domain Models (SDM) with persona profiles, state machines, and business policies.
"""

from typing import Dict, Any, Optional
from chronos.core.types import StructuralDomainModel, BehavioralDomainModel
from chronos.enrichment.persona import PersonaMatrixBuilder
from chronos.enrichment.fsm import FSMEngineBuilder
from chronos.enrichment.rules import BusinessRuleBuilder

class SemanticEnrichmentEngine:
    """Orchestrates offline semantic enrichment to produce a BehavioralDomainModel AST."""

    def __init__(self, ai_provider=None, ontology_catalog=None):
        self.ai_provider = ai_provider
        self.ontology_catalog = ontology_catalog

    def enrich(self, sdm: StructuralDomainModel, custom_config: Optional[Dict[str, Any]] = None) -> BehavioralDomainModel:
        bdm = BehavioralDomainModel(structural_model=sdm)

        # 1. Bind Persona Matrix
        bdm.personas = PersonaMatrixBuilder.build_default_personas(sdm)

        # 2. Bind State Machine Lifecycles
        bdm.state_machines = FSMEngineBuilder.build_default_fsms(sdm)

        # 3. Bind Business Invariants and Temporal Schedules
        rules, schedules = BusinessRuleBuilder.build_default_rules_and_schedules(sdm)
        bdm.rules = rules
        bdm.schedules = schedules

        return bdm
