from typing import Dict, Any
from ..providers.contracts import SystemSpec, PatchPlan, PRDraft, PolicyFacts

def plan_pipeline(job: Dict[str, Any]) -> Dict[str, Any]:
    # Placeholder: upstream planner would be called here (OpenAI structured outputs)
    # Return a minimal SystemSpec-like dict for demo.
    spec = SystemSpec(
        title=job.get("title","Untitled"),
        summary="Planned via planner lane",
        architecture={"components":["api","worker","ui"]},
        non_functional={"security":"owasp-baseline"},
        acceptance_criteria=["boot app","run tests"],
        evidence=[]
    )
    return spec.model_dump()

def exec_pipeline(spec: Dict[str, Any], facts: PolicyFacts) -> Dict[str, Any]:
    # Placeholder: downstream execution (Claude sub-agents) would create a PatchPlan
    plan = PatchPlan(changes=[], tests_added=["tests/test_smoke.py"], notes="demo")
    pr = PRDraft(title=f"Implement {spec.get('title')}", body_md="Demo PR", linked_issues=[])
    return {"patch_plan": plan.model_dump(), "pr": pr.model_dump()}
