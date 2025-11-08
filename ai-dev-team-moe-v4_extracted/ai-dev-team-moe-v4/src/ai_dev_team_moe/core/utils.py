
from __future__ import annotations
from typing import Any, Dict
import yaml
from dataclasses import dataclass

def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@dataclass
class CostCaps:
    max_cost_usd: float
    max_latency_s: int
