"""
Finite State Machine (FSM) Domain Rule Builder.
"""

from typing import Dict
from chronos.core.types import StateMachineDef, StateTransition, StructuralDomainModel

class FSMEngineBuilder:
    """Instantiates domain-appropriate FSM lifecycles for entities."""

    @staticmethod
    def build_default_fsms(sdm: StructuralDomainModel) -> Dict[str, StateMachineDef]:
        fsms: Dict[str, StateMachineDef] = {}

        if "TB_STUDENT" in sdm.tables:
            fsms["FSM_STUDENT_LIFECYCLE"] = StateMachineDef(
                name="FSM_STUDENT_LIFECYCLE",
                target_entity="TB_STUDENT",
                initial_state="ENROLLED",
                states=["ENROLLED", "ACADEMIC_PROBATION", "GRADUATED", "SUSPENDED"],
                transitions=[
                    StateTransition("ENROLLED", "ACADEMIC_PROBATION", "cgpa < 5.0"),
                    StateTransition("ACADEMIC_PROBATION", "ENROLLED", "cgpa >= 5.0"),
                    StateTransition("ENROLLED", "GRADUATED", "completed_credits >= 120")
                ]
            )

        return fsms
