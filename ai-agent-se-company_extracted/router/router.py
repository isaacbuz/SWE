import yaml, json
from typing import Dict, Any

class Router:
    def __init__(self, policy_path: str):
        with open(policy_path, "r", encoding="utf-8") as f:
            self.policy = yaml.safe_load(f)

    def route(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # naive rule matcher
        for rule in self.policy.get("rules", []):
            cond = rule.get("match", {})
            if all(task.get(k) == v for k, v in cond.items()):
                return {**self.policy["defaults"], **rule.get("route", {})}
        return self.policy["defaults"]
