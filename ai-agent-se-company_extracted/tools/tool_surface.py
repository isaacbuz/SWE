from typing import List, Dict, Any

class ToolSurface:
    def __init__(self):
        # In production these would call GitHub, CI, security scanners, etc.
        pass

    def read_repo(self, paths: List[str], max_bytes: int = 500000) -> Dict[str, Any]:
        return {"paths": paths, "content": "/* stub */"}

    def apply_patch(self, unified_diff: str, strategy: str = "clean") -> Dict[str, Any]:
        return {"applied": True, "strategy": strategy}

    def run_tests(self, targets: List[str], coverage_min: float = 0.7) -> Dict[str, Any]:
        return {"passed": True, "coverage": 0.82}

    def create_pr(self, title: str, body_md: str, branch: str, base: str, closes: List[int]) -> Dict[str, Any]:
        return {"url": "https://github.com/org/repo/pull/1", "title": title, "closes": closes}

    def render_diagram(self, mermaid: str, out: str = "svg") -> Dict[str, Any]:
        return {"artifact": "diagram.svg", "status": "rendered"}
