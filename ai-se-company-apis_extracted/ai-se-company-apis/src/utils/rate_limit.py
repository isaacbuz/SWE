from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

class RateLimitError(Exception): ...
class ServerError(Exception): ...

def classify(resp: httpx.Response):
    if resp.status_code == 429:
        raise RateLimitError("rate limited")
    if 500 <= resp.status_code < 600:
        raise ServerError(f"server error {resp.status_code}")
    resp.raise_for_status()

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type((RateLimitError, ServerError, httpx.HTTPError))
)
def robust_get(client: httpx.Client, url: str, **kw):
    r = client.get(url, **kw)
    classify(r)
    return r
