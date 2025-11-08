
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class AgentResult:
    role: str
    model: str
    summary: str
    details: Dict[str, Any]

class BaseAgent:
    role: str = "base"
    def __init__(self, model_id: str):
        self.model_id = model_id
    def run(self, prompt: str) -> AgentResult:
        # Stub: integrate your LLM call here
        return AgentResult(role=self.role, model=self.model_id, summary=f"{self.role} processed.", details={})
