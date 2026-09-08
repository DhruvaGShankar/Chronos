"""
Chronos Simulation Identity & Cryptographic Hashes Engine.
Computes deterministic SHA-256 identity tokens ensuring 100% reproducible simulation experiments.
"""

import hashlib
import json
from typing import Dict, Any

class SimulationIdentity:
    """Computes reproducible cryptographic identity hashes for simulation runs."""

    @staticmethod
    def compute_hash(data: Any) -> str:
        """Computes a SHA-256 hash token for any JSON-serializable structure or string."""
        if isinstance(data, dict) or isinstance(data, list):
            serialized = json.dumps(data, sort_keys=True)
        else:
            serialized = str(data)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    @classmethod
    def generate_simulation_id(
        cls,
        schema_hash: str,
        semantic_model_hash: str,
        ir_version: str,
        compiler_version: str,
        root_seed: int,
        runtime_version: str = "2.1.0"
    ) -> str:
        """Generates a composite cryptographic Simulation ID."""
        composite_payload = {
            "schema_hash": schema_hash,
            "semantic_model_hash": semantic_model_hash,
            "ir_version": ir_version,
            "compiler_version": compiler_version,
            "root_seed": root_seed,
            "runtime_version": runtime_version
        }
        full_hash = cls.compute_hash(composite_payload)
        return f"sim_0x{full_hash[:16]}"
