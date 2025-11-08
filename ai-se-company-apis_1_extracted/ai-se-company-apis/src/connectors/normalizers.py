from typing import Dict, Any
from ..providers.contracts import SystemSpec, Evidence

def normalize_google_sheet_to_spec(data: Dict[str, Any]) -> SystemSpec:
    # Minimal example: expect first column key, second column value
    values = data.get("values", [])
    kv = {row[0]: (row[1] if len(row)>1 else "") for row in values if row}
    spec = SystemSpec(
        title=kv.get("title","Untitled"),
        summary=kv.get("summary",""),
        architecture={"components": kv.get("architecture","").split(",") if kv.get("architecture") else []},
        non_functional={"notes": kv.get("nfr","")},
        acceptance_criteria=[s.strip() for s in kv.get("acceptance","").split("|") if s.strip()],
        evidence=[Evidence(source_url="google_sheets://", snippet="from sheet")]
    )
    return spec
