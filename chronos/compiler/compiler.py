"""
Master Chronos IR Compiler Pipeline Manager.
"""

from chronos.core.types import BehavioralDomainModel, ChronosIR
from chronos.compiler.passes import CompilerPasses

class ChronosCompiler:
    """Compiles enriched Behavioral Domain Models into executable Chronos IR."""

    def __init__(self, root_seed: int = 1337):
        self.root_seed = root_seed

    def compile(self, bdm: BehavioralDomainModel) -> ChronosIR:
        """Runs compilation passes and emits Chronos IR."""
        # 1. Structural Verification Pass
        CompilerPasses.verify_structural_integrity(bdm)

        # 2. Lowering & Bytecode Emission Pass
        return CompilerPasses.lower_to_ir(bdm, self.root_seed)
