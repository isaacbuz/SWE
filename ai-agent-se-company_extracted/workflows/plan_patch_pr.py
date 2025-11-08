from typing import Dict, Any
from providers.openai_client import OpenAIPlanner
from providers.anthropic_client import AnthropicExecutor
from tools.tool_surface import ToolSurface
from contracts.models import PatchPlan

def run_plan_patch_pr(user_request: str, openai_key: str, anthropic_key: str) -> Dict[str, Any]:
    planner = OpenAIPlanner(openai_key)
    execu = AnthropicExecutor(anthropic_key)
    tools = ToolSurface()

    spec = planner.plan(user_request)
    # synthesize a tiny patch plan for demo purposes
    plan = PatchPlan(repo="org/repo", changes=[
        {"paths": ["gateway/app.py"], "rationale": "add health route", "methods": ["apply_diff"], "avoid_paths": []}
    ], constraints={"max_files": 5})
    result = execu.execute_patch_plan(plan.dict())

    pr = tools.create_pr(**result["PRDraft"])
    return {"spec": spec, "pr": pr}
