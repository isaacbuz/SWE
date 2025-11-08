import httpx, os, hashlib, time
from typing import List, Dict, Any, Iterable

ALLOWED_FILES = {"README.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE", "CODE_OF_CONDUCT.md"}

def _h(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()

def filter_repos(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in repos:
        if r.get("stargazers_count",0) >= 2000 and not r.get("archived", False):
            out.append(r)
    return out

def chunk_text(text: str, size: int = 1200, overlap: int = 120) -> Iterable[str]:
    i=0
    while i < len(text):
        yield text[i:i+size]
        i += size - overlap
