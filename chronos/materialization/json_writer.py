"""
JSON Event Stream & Entity State Exporter.
"""

import os
import json
from dataclasses import asdict
from typing import Dict, List, Any
from chronos.materialization.base import BaseMaterializer
from chronos.core.types import CausalEvent

class JSONMaterializer(BaseMaterializer):
    """Exports entity graphs and causal event streams into JSON files."""

    def materialize(self, entity_store: Dict[str, List[Dict[str, Any]]], event_log: List[CausalEvent], target_path: str = "output/simulation_dump.json"):
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

        payload = {
            "entity_store": entity_store,
            "event_log": [asdict(e) for e in event_log]
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        print(f"  [JSON Materializer] Exported JSON snapshot to: {target_path}")
