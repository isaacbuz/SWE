import yaml, os
from typing import Dict, Any

class Router:
    def __init__(self, providers_yaml_path: str):
        with open(providers_yaml_path, "r") as f:
            self.cfg = yaml.safe_load(f)

    def decide(self, job: Dict[str, Any]) -> Dict[str, bool]:
        # naive example: enable lanes based on config and job tags
        p = self.cfg.get("providers", {})
        tags = set(job.get("tags", []))
        return {
            "use_google": p.get("google",{}).get("enabled", False) and ("google" in tags or "sheet" in tags),
            "use_gsa": p.get("us_gov_gsa",{}).get("enabled", False) and ("gsa" in tags or "gov" in tags),
            "use_github_rag": p.get("github_public",{}).get("enabled", False) and ("rag" in tags or "guides" in tags),
        }
