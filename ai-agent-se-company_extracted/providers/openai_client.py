# Stub: OpenAI structured outputs planning lane
from typing import Dict, Any
from contracts.models import ArchitecturePlan, IssueList, Issue, ADR, Component, Risk

class OpenAIPlanner:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def plan(self, request: str) -> Dict[str, Any]:
        # Return a synthetic sample compliant with schemas
        plan = ArchitecturePlan(
            project="sample",
            goals=["deliver value","maintainability"],
            decisions=[ADR(adr_id="ADR-0001", title="Use FastAPI", status="accepted")],
            components=[Component(name="gateway", tech="FastAPI", responsibilities=["auth","rate_limit"])],
            risks=[Risk(id="R-1", severity="medium", mitigation="fallback routes")]
        )
        issues = IssueList(repo="org/repo", items=[
            Issue(title="Init FastAPI", description="Create gateway app", labels=["feature"], estimate_hours=2.0),
            Issue(title="Router v1", description="Implement policy eval", labels=["feature"], estimate_hours=3.0)
        ])
        return {"ArchitecturePlan": plan.dict(), "IssueList": issues.dict()}
