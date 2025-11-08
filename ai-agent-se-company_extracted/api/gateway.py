from fastapi import FastAPI
from pydantic import BaseModel
from workflows.plan_patch_pr import run_plan_patch_pr

app = FastAPI()

class BuildRequest(BaseModel):
    request: str
    openai_key: str = "env"
    anthropic_key: str = "env"

@app.post("/build")
def build(req: BuildRequest):
    # This would read keys from env/secret manager in production
    result = run_plan_patch_pr(req.request, req.openai_key, req.anthropic_key)
    return {"ok": True, "result": result}
