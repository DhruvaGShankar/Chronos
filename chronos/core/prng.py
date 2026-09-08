"""
Hierarchical PRNG Seed Engine.
Guarantees bit-exact simulation determinism independent of OS, hardware, or thread scheduling.
"""

import random
import hashlib

class PRNGSeedTree:
    """Derives deterministic sub-seeds hierarchically from a master root seed."""

    def __init__(self, root_seed: int):
        self.root_seed = root_seed

    def derive_entity_seed(self, entity_type: str, entity_index: int) -> int:
        """Derives a unique, deterministic seed for an individual entity instance."""
        token = f"ROOT_{self.root_seed}::ENTITY_{entity_type}::{entity_index}"
        hash_bytes = hashlib.sha256(token.encode('utf-8')).digest()
        return int.from_bytes(hash_bytes[:8], byteorder='big')

    def derive_event_seed(self, entity_seed: int, tick: int, event_name: str) -> int:
        """Derives a deterministic seed for a specific event tick instance."""
        token = f"SEED_{entity_seed}::TICK_{tick}::EVT_{event_name}"
        hash_bytes = hashlib.sha256(token.encode('utf-8')).digest()
        return int.from_bytes(hash_bytes[:8], byteorder='big')

    def get_prng(self, seed: int) -> random.Random:
        """Returns a seeded Python Random instance."""
        return random.Random(seed)
