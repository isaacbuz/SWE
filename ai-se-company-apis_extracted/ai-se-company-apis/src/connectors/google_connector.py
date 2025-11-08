import httpx, os, json, time
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from .normalizers import normalize_google_sheet_to_spec

class GoogleConnector:
    def __init__(self, token_getter):
        self.token_getter = token_getter
        self.base = "https://sheets.googleapis.com/v4"

    def _headers(self) -> Dict[str, str]:
        token = self.token_getter()
        return {"Authorization": f"Bearer {token}"}

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=30))
    def read_sheet(self, spreadsheet_id: str, range_a1: str) -> Dict[str, Any]:
        url = f"{self.base}/spreadsheets/{spreadsheet_id}/values/{range_a1}"
        r = httpx.get(url, headers=self._headers(), timeout=30)
        r.raise_for_status()
        return r.json()

    def sheet_to_spec(self, spreadsheet_id: str, range_a1: str):
        data = self.read_sheet(spreadsheet_id, range_a1)
        return normalize_google_sheet_to_spec(data)
