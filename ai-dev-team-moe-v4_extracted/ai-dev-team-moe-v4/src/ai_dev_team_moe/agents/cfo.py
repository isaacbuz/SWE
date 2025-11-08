
from .base import BaseAgent, AgentResult

class Agent(BaseAgent):
    role = "cfo"
    def run(self, prompt: str) -> AgentResult:
        # Replace with actual LLM invocation for cfo
        return AgentResult(role=self.role, model=self.model_id, summary="OK", details={"note": "stub"})
