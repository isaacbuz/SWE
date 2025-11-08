from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Evidence(BaseModel):
    source_url: str
    snippet: Optional[str] = None
    license: Optional[str] = None
    last_updated: Optional[str] = None
    sha: Optional[str] = None

class PolicyFacts(BaseModel):
    facts: Dict[str, Any] = {}
    evidence: List[Evidence] = []

class SystemSpec(BaseModel):
    title: str
    summary: str
    architecture: Dict[str, Any]
    non_functional: Dict[str, Any]
    acceptance_criteria: List[str] = []
    evidence: List[Evidence] = []

class Task(BaseModel):
    id: str
    title: str
    description: str
    estimate_hrs: float = 1.0
    evidence: List[Evidence] = []

class Backlog(BaseModel):
    epic: str
    stories: List[Task] = []

class FileChange(BaseModel):
    path: str
    change_type: str  # add|modify|delete
    content: Optional[str] = None
    patch: Optional[str] = None
    rationale: Optional[str] = None
    evidence: List[Evidence] = []

class PatchPlan(BaseModel):
    changes: List[FileChange]
    tests_added: List[str] = []
    notes: Optional[str] = None

class PRDraft(BaseModel):
    title: str
    body_md: str
    linked_issues: List[str] = []
