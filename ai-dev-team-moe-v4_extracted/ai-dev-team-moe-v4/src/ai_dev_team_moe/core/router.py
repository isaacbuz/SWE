
from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass
from .utils import load_yaml

@dataclass
class RouteDecision:
    role: str
    suggested: str
    fallback_chain: List[str]
    rationale: str

class MoERouter:
    def __init__(self, models_path: str, settings_path: str):
        self.registry = load_yaml(models_path)
        self.settings = load_yaml(settings_path)
        self.catalog = self.registry.get("catalog", {})
        self.roles = self.registry.get("roles", {})

    def route_for_role(self, role: str, constraints: Dict[str, Any] | None = None) -> RouteDecision:
        constraints = constraints or {}
        prefer = self.roles.get(role, {}).get("prefer", [])
        fallback = self.roles.get(role, {}).get("fallback", [])
        diversify = self.settings.get("routing", {}).get("diversify_vendors", True)
        rationale = []

        # Simple heuristic: honor prefer unless cost cap is exceeded by pricing hints
        max_cost = self.settings.get("run", {}).get("max_cost_usd", 5.0)
        chosen = None
        for mid in prefer + fallback:
            price = self.catalog.get(mid, {}).get("pricing_usd_per_mtok", {}).get("input", 0.05)
            if price * 1.0 <= max_cost:  # placeholder screening
                chosen = mid
                break
        if not chosen and (prefer or fallback):
            chosen = (prefer + fallback)[0]

        rationale.append(f"Selected {chosen} for role {role} within cost cap ${max_cost}.")
        return RouteDecision(role=role, suggested=chosen, fallback_chain=fallback, rationale="\n".join(rationale))

    def plan_assignment(self) -> Dict[str, RouteDecision]:
        decisions = {}
        for role in self.roles.keys():
            decisions[role] = self.route_for_role(role)
        return decisions
