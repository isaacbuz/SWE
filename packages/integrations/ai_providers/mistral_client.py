"""
Mistral AI Integration

Implements the AIProvider interface for Mistral AI models.
Supports Mistral Large, Medium, Small with streaming and function calling.
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


class MistralClient(AIProvider):
    """
    Mistral AI API client.

    Features:
    - Mistral Large, Medium, Small models
    - Function calling
    - Streaming support
    - JSON mode
    """

    # Model catalog
    MODELS = {
        "mistral-large-latest": ModelInfo(
            id="mistral-large-latest",
            name="Mistral Large",
            context_window=32000,
            max_output_tokens=8192,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
            ],
            cost_per_1k_prompt_tokens=0.002,
            cost_per_1k_completion_tokens=0.006,
            supports_system_prompt=True,
        ),
        "mistral-medium-latest": ModelInfo(
            id="mistral-medium-latest",
            name="Mistral Medium",
            context_window=32000,
            max_output_tokens=8192,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
            ],
            cost_per_1k_prompt_tokens=0.001,
            cost_per_1k_completion_tokens=0.003,
            supports_system_prompt=True,
        ),
        "mistral-small-latest": ModelInfo(
            id="mistral-small-latest",
            name="Mistral Small",
            context_window=32000,
            max_output_tokens=8192,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
            ],
            cost_per_1k_prompt_tokens=0.0002,
            cost_per_1k_completion_tokens=0.0006,
            supports_system_prompt=True,
        ),
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.mistral.ai/v1",
        timeout: int = 300,
    ):
        """
        Initialize Mistral client.

        Args:
            api_key: Mistral API key (or use MISTRAL_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("Mistral API key required. Set MISTRAL_API_KEY env var or pass api_key.")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

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
        """Generate completion from Mistral model."""
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model {model} not found")

        # Prepare messages
        mistral_messages = []
        if system_prompt:
            mistral_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            mistral_messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        # Prepare request
        request_data = {
            "model": model,
            "messages": mistral_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            request_data["response_format"] = {"type": "json_object"}

        if tools:
            request_data["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                }
                for tool in tools
            ]

        if stop_sequences:
            request_data["stop"] = stop_sequences

        try:
            response = await self.client.post("/chat/completions", json=request_data)
            response.raise_for_status()
            data = response.json()

            # Extract response
            choice = data["choices"][0]
            message = choice["message"]
            content = message.get("content", "")

            # Extract tool calls
            tool_calls = None
            if "tool_calls" in message:
                tool_calls = [
                    ToolCall(
                        id=tc["id"],
                        name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"]),
                    )
                    for tc in message["tool_calls"]
                ]

            # Extract usage
            usage_data = data.get("usage", {})
            usage = Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

            return Completion(
                id=data["id"],
                content=content,
                model=model,
                usage=usage,
                finish_reason=choice.get("finish_reason", "stop"),
                tool_calls=tool_calls,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid Mistral API key")
            elif e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                raise RateLimitError(retry_after=retry_after)
            elif e.response.status_code == 400:
                raise InvalidRequestError(f"Invalid request: {e.response.text}")
            else:
                raise AIProviderError(f"Mistral API error: {e.response.text}")

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
        """Stream completion from Mistral model."""
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model {model} not found")

        # Prepare messages (same as complete)
        mistral_messages = []
        if system_prompt:
            mistral_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            mistral_messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        request_data = {
            "model": model,
            "messages": mistral_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if tools:
            request_data["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                }
                for tool in tools
            ]

        try:
            async with self.client.stream("POST", "/chat/completions", json=request_data) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            choice = data.get("choices", [{}])[0]
                            delta = choice.get("delta", {})

                            content = delta.get("content", "")
                            finish_reason = choice.get("finish_reason")

                            yield StreamChunk(
                                content=content,
                                finish_reason=finish_reason,
                            )
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid Mistral API key")
            elif e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                raise RateLimitError(retry_after=retry_after)
            else:
                raise AIProviderError(f"Mistral API error: {e.response.text}")

    def list_models(self) -> List[ModelInfo]:
        """List available Mistral models."""
        return list(self.MODELS.values())

    async def health_check(self) -> bool:
        """Check if Mistral API is healthy."""
        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

