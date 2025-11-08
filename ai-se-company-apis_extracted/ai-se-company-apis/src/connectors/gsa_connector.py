import httpx, os
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

class GsaConnector:
    def __init__(self, api_key: str, base_url: str = "https://api.gsa.gov"):
        self.api_key = api_key
        self.base = base_url

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=30))
    def fetch(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"X-API-Key": self.api_key}
        url = f"{self.base}/{endpoint.lstrip('/')}"
        r = httpx.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
