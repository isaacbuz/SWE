"""
GitHub API Client

Provides async GitHub API client with:
- Token and GitHub App authentication
- Rate limiting compliance
- REST and GraphQL support
- Webhook signature verification
"""

import asyncio
import hashlib
import hmac
import time
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass


class GitHubClient:
    """
    Async GitHub API client with authentication and rate limiting

    Supports:
    - Personal access tokens
    - GitHub App authentication
    - OAuth tokens
    - Rate limit compliance
    - GraphQL queries
    """

    def __init__(
        self,
        token: Optional[str] = None,
        app_id: Optional[str] = None,
        private_key: Optional[str] = None,
        base_url: str = "https://api.github.com",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub client

        Args:
            token: Personal access token or OAuth token
            app_id: GitHub App ID
            private_key: GitHub App private key (PEM format)
            base_url: GitHub API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.token = token
        self.app_id = app_id
        self.private_key = private_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # Rate limiting
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
        self.rate_limit_lock = asyncio.Lock()

        # GraphQL endpoint
        self.graphql_url = urljoin(base_url, "/graphql")

    def _get_headers(self, installation_id: Optional[str] = None) -> Dict[str, str]:
        """Get headers for API request"""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        elif self.app_id and self.private_key and installation_id:
            # Generate JWT for GitHub App
            token = self._generate_app_token(installation_id)
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def _generate_app_token(self, installation_id: str) -> str:
        """
        Generate JWT token for GitHub App authentication

        Args:
            installation_id: GitHub App installation ID

        Returns:
            JWT token
        """
        # In production, use PyJWT library
        # This is a placeholder for the token generation logic
        import jwt
        from datetime import datetime, timedelta

        payload = {
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(minutes=10)).timestamp()),
            "iss": self.app_id,
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def _check_rate_limit(self):
        """Check and wait for rate limit if necessary"""
        async with self.rate_limit_lock:
            if self.rate_limit_remaining <= 1:
                wait_time = max(0, self.rate_limit_reset - time.time())
                if wait_time > 0:
                    await asyncio.sleep(wait_time + 1)

    def _update_rate_limit(self, headers: Dict[str, str]):
        """Update rate limit info from response headers"""
        if "x-ratelimit-remaining" in headers:
            self.rate_limit_remaining = int(headers["x-ratelimit-remaining"])
        if "x-ratelimit-reset" in headers:
            self.rate_limit_reset = int(headers["x-ratelimit-reset"])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=60))
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        installation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Make async HTTP request to GitHub API

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/repos/owner/repo/issues")
            params: Query parameters
            json: JSON body
            installation_id: GitHub App installation ID

        Returns:
            Response JSON

        Raises:
            RateLimitError: If rate limit is exceeded
            httpx.HTTPError: If request fails
        """
        await self._check_rate_limit()

        url = urljoin(self.base_url, endpoint.lstrip("/"))
        headers = self._get_headers(installation_id)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
            )

            # Update rate limit
            self._update_rate_limit(response.headers)

            # Check for rate limit
            if response.status_code == 403 and "rate limit" in response.text.lower():
                raise RateLimitError("GitHub API rate limit exceeded")

            response.raise_for_status()

            # Handle empty responses
            if response.status_code == 204:
                return {}

            return response.json()

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request"""
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST request"""
        return await self.request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """PUT request"""
        return await self.request("PUT", endpoint, **kwargs)

    async def patch(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """PATCH request"""
        return await self.request("PATCH", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request"""
        return await self.request("DELETE", endpoint, **kwargs)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=60))
    async def graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        installation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute GraphQL query

        Args:
            query: GraphQL query string
            variables: Query variables
            installation_id: GitHub App installation ID

        Returns:
            GraphQL response data

        Raises:
            Exception: If query returns errors
        """
        await self._check_rate_limit()

        headers = self._get_headers(installation_id)
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.graphql_url,
                headers=headers,
                json=payload,
            )

            self._update_rate_limit(response.headers)
            response.raise_for_status()

            data = response.json()

            if "errors" in data:
                raise Exception(f"GraphQL errors: {data['errors']}")

            return data.get("data", {})

    async def paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        per_page: int = 100,
        max_pages: Optional[int] = None,
    ) -> list:
        """
        Paginate through API results

        Args:
            endpoint: API endpoint
            params: Query parameters
            per_page: Items per page
            max_pages: Maximum number of pages to fetch

        Returns:
            List of all items
        """
        params = params or {}
        params["per_page"] = per_page
        params["page"] = 1

        all_items = []
        page_count = 0

        while True:
            response = await self.get(endpoint, params=params)

            if not response:
                break

            # Handle both list responses and paginated dict responses
            if isinstance(response, list):
                items = response
            elif isinstance(response, dict) and "items" in response:
                items = response["items"]
            else:
                items = [response]

            all_items.extend(items)

            if not items or len(items) < per_page:
                break

            page_count += 1
            if max_pages and page_count >= max_pages:
                break

            params["page"] += 1

        return all_items

    @staticmethod
    def verify_webhook_signature(
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Verify GitHub webhook signature

        Args:
            payload: Raw webhook payload bytes
            signature: X-Hub-Signature-256 header value
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        if not signature.startswith("sha256="):
            return False

        expected_signature = hmac.new(
            key=secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()

        received_signature = signature.split("=", 1)[1]

        return hmac.compare_digest(expected_signature, received_signature)

    async def get_rate_limit(self) -> Dict[str, Any]:
        """
        Get current rate limit status

        Returns:
            Rate limit information
        """
        return await self.get("/rate_limit")

    async def get_authenticated_user(self) -> Dict[str, Any]:
        """
        Get authenticated user information

        Returns:
            User information
        """
        return await self.get("/user")
