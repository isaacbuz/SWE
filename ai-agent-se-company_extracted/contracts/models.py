from pydantic import BaseModel, Field, HttpUrl, conlist, validator
from typing import List, Optional, Literal, Dict, Any

class ADR(BaseModel):
    adr_id: str
    title: str
    status: Literal["accepted", "rejected", "proposed"]
    context: Optional[str] = ""
    decision: Optional[str] = ""
    consequences: Optional[str] = ""

class Risk(BaseModel):
    id: str
    severity: Literal["low","medium","high","critical"]
    mitigation: str

class Component(BaseModel):
    name: str
    tech: str
    responsibilities: List[str]

class ArchitecturePlan(BaseModel):
    project: str
    goals: List[str]
    decisions: List[ADR] = []
    components: List[Component] = []
    risks: List[Risk] = []

class Issue(BaseModel):
    title: str
    description: str
    labels: List[str] = []
    estimate_hours: float = 1.0

class IssueList(BaseModel):
    repo: str
    items: List[Issue]

class PatchChange(BaseModel):
    paths: List[str]
    rationale: str
    methods: conlist(Literal["apply_diff","add_tests","refactor"], min_items=1)
    avoid_paths: List[str] = []

class PatchPlan(BaseModel):
    repo: str
    changes: List[PatchChange]
    constraints: Dict[str, Any] = {}

class ComplianceReport(BaseModel):
    secrets_scan: Dict[str, Any]
    licenses: Dict[str, Any]
    cve: Dict[str, Any]

class PRDraft(BaseModel):
    title: str
    body_md: str
    branch: str = "ai-implementation"
    base: str = "main"
    closes: List[int] = []
