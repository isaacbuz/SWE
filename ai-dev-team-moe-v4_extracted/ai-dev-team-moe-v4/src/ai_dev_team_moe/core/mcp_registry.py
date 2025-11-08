
from __future__ import annotations
from typing import Dict, List, Any
from .utils import load_yaml

class MCPRegistry:
    def __init__(self, path: str):
        self.spec = load_yaml(path)
    def list_tools(self) -> List[Dict[str, Any]]:
        return self.spec.get("tools", [])
