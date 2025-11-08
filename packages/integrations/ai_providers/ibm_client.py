"""
IBM Granite Integration

Implements the AIProvider interface for IBM's Granite Code models.
Supports watsonx.ai integration with code-specific optimizations.
"""

import os
import json
import logging
from typing import AsyncIterator, Dict, List, Optional, Any

import httpx

from .base import (
    AIProvider,
    Completion,
    StreamChunk,
    Message,
    Tool,
    ToolCall,
    Usage,
    ModelInfo,
    ModelCapability,
    AIProviderError,
    RateLimitError,
    AuthenticationError,
    InvalidRequestError,
    ModelNotFoundError,
)

logger = logging.getLogger(__name__)


class IBMClient(AIProvider):
    """
    IBM Granite API client for watsonx.ai.

    Features:
    - Granite Code models optimized for code generation
    - Integration with watsonx.ai platform
    - Support for code completion, debugging, and explanation
    - Enterprise-grade security and governance
    """

    # Model catalog
    MODELS = {
        "granite-20b-code-instruct": ModelInfo(
            id="granite-20b-code-instruct",
            name="Granite 20B Code Instruct",
            context_window=8192,
            max_output_tokens=4096,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.CODE_EXECUTION,
            ],
            cost_per_1k_prompt_tokens=0.002,  # Approximate
            cost_per_1k_completion_tokens=0.008,
            supports_system_prompt=True,
        ),
        "granite-34b-code-instruct": ModelInfo(
            id="granite-34b-code-instruct",
            name="Granite 34B Code Instruct",
            context_window=8192,
            max_output_tokens=4096,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.CODE_EXECUTION,
            ],
            cost_per_1k_prompt_tokens=0.003,
            cost_per_1k_completion_tokens=0.012,
            supports_system_prompt=True,
        ),
        "granite-3b-code-base": ModelInfo(
            id="granite-3b-code-base",
            name="Granite 3B Code Base",
            context_window=8192,
            max_output_tokens=4096,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
            ],
            cost_per_1k_prompt_tokens=0.0005,
            cost_per_1k_completion_tokens=0.002,
            supports_system_prompt=False,
        ),
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: str = "https://us-south.ml.cloud.ibm.com",
        timeout: float = 300.0,
        max_retries: int = 3,
    ):
        """
        Initialize IBM Granite client.

        Args:
            api_key: IBM Cloud API key (defaults to IBM_API_KEY env var)
            project_id: watsonx.ai project ID (defaults to IBM_PROJECT_ID env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.api_key = api_key or os.getenv("IBM_API_KEY")
        self.project_id = project_id or os.getenv("IBM_PROJECT_ID")

        if not self.api_key:
            raise ValueError("IBM API key is required")
        if not self.project_id:
            raise ValueError("IBM project ID is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._access_token = None

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
        )

    async def _get_access_token(self) -> str:
        """Get IBM Cloud IAM access token."""
        if self._access_token:
            # TODO: Add token expiry check
            return self._access_token

        iam_url = "https://iam.cloud.ibm.com/identity/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": self.api_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(iam_url, headers=headers, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data["access_token"]
                return self._access_token
            else:
                raise AuthenticationError("Failed to obtain IBM Cloud access token")

    def _format_messages(self, messages: List[Message]) -> str:
        """Convert Message objects to prompt string for Granite."""
        # Granite Code models use a specific prompt format
        prompt_parts = []

        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"Question: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Answer: {msg.content}")

        # Add final prompt for assistant response
        prompt_parts.append("Answer:")

        return "\n\n".join(prompt_parts)

    async def complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Tool]] = None,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> Completion:
        """
        Generate a completion using Granite.

        Args:
            messages: Conversation messages
            model: Model ID (e.g., 'granite-20b-code-instruct')
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            tools: Optional tools (not supported by Granite)
            system_prompt: Optional system prompt
            json_mode: Force JSON output (via prompt engineering)
            stop_sequences: Optional stop sequences
            **kwargs: Additional IBM-specific parameters

        Returns:
            Completion object
        """
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")

        if tools:
            logger.warning("Granite models do not support native function calling")

        # Get access token
        token = await self._get_access_token()

        # Add system prompt to messages if provided
        if system_prompt:
            messages = [Message(role="system", content=system_prompt)] + messages

        # Format messages into prompt
        prompt = self._format_messages(messages)

        # Build request payload
        payload = {
            "model_id": model,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy" if temperature == 0 else "sample",
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "min_new_tokens": 1,
            },
            "project_id": self.project_id,
        }

        if stop_sequences:
            payload["parameters"]["stop_sequences"] = stop_sequences

        # Add any additional kwargs to parameters
        if kwargs:
            payload["parameters"].update(kwargs)

        # Make API request with retries
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    "/ml/v1/text/generation",
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [{}])[0]

                    content = results.get("generated_text", "")
                    token_count = results.get("generated_token_count", 0)
                    input_token_count = results.get("input_token_count", 0)

                    usage = Usage(
                        prompt_tokens=input_token_count,
                        completion_tokens=token_count,
                        total_tokens=input_token_count + token_count,
                    )

                    finish_reason_map = {
                        "EOS_TOKEN": "stop",
                        "MAX_TOKENS": "length",
                        "STOP_SEQUENCE": "stop",
                    }
                    finish_reason = results.get("stop_reason", "EOS_TOKEN")
                    finish_reason = finish_reason_map.get(finish_reason, "stop")

                    return Completion(
                        id=data.get("model_id", ""),
                        content=content.strip(),
                        model=model,
                        usage=usage,
                        finish_reason=finish_reason,
                    )

                elif response.status_code == 429:
                    raise RateLimitError()
                elif response.status_code == 401 or response.status_code == 403:
                    # Token might be expired, clear it
                    self._access_token = None
                    raise AuthenticationError("Authentication failed")
                elif response.status_code == 400:
                    error_data = response.json()
                    raise InvalidRequestError(error_data.get("message", "Invalid request"))
                elif response.status_code == 404:
                    raise ModelNotFoundError(f"Model '{model}' not found")
                else:
                    response.raise_for_status()

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt == self.max_retries - 1:
                    raise AIProviderError(f"Network error after {self.max_retries} attempts: {e}")
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                continue

        raise AIProviderError("Max retries exceeded")

    async def stream_complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Tool]] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """
        Generate a streaming completion using Granite.

        Yields:
            StreamChunk objects with incremental content
        """
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")

        # Get access token
        token = await self._get_access_token()

        # Add system prompt to messages if provided
        if system_prompt:
            messages = [Message(role="system", content=system_prompt)] + messages

        # Format messages into prompt
        prompt = self._format_messages(messages)

        # Build request payload
        payload = {
            "model_id": model,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy" if temperature == 0 else "sample",
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "min_new_tokens": 1,
            },
            "project_id": self.project_id,
        }

        if kwargs:
            payload["parameters"].update(kwargs)

        # Make streaming request
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        async with self.client.stream(
            "POST",
            "/ml/v1/text/generation_stream",
            json=payload,
            headers=headers,
        ) as response:
            if response.status_code != 200:
                if response.status_code == 429:
                    raise RateLimitError()
                elif response.status_code == 401 or response.status_code == 403:
                    raise AuthenticationError("Authentication failed")
                else:
                    response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip() or not line.startswith("data: "):
                    continue

                data = line[6:]  # Remove "data: " prefix

                try:
                    event = json.loads(data)
                    results = event.get("results", [{}])[0]

                    if "generated_text" in results:
                        yield StreamChunk(content=results["generated_text"])

                    if results.get("stop_reason"):
                        yield StreamChunk(content="", finish_reason="stop")

                except json.JSONDecodeError:
                    continue

    async def count_tokens(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Tool]] = None
    ) -> int:
        """
        Count tokens (approximation for Granite).

        IBM watsonx.ai doesn't provide a dedicated tokenization endpoint,
        so we use character-based approximation.
        """
        prompt = self._format_messages(messages)
        # Rough approximation: 4 characters per token
        return len(prompt) // 4

    def get_model_info(self, model: str) -> ModelInfo:
        """Get information about a specific Granite model."""
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")
        return self.MODELS[model]

    def list_models(self) -> List[ModelInfo]:
        """List all available Granite models."""
        return list(self.MODELS.values())

    async def health_check(self) -> bool:
        """Check if IBM watsonx.ai API is available."""
        try:
            token = await self._get_access_token()
            return token is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
