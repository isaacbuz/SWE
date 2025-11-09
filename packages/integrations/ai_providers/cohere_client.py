"""
Cohere Integration

Implements the AIProvider interface for Cohere models.
Supports Command, Command R+ with streaming and function calling.
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


class CohereClient(AIProvider):
    """
    Cohere API client.

    Features:
    - Command, Command R+ models
    - Function calling
    - Streaming support
    - RAG capabilities
    """

    # Model catalog
    MODELS = {
        "command-r-plus": ModelInfo(
            id="command-r-plus",
            name="Command R+",
            context_window=128000,
            max_output_tokens=4096,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
            ],
            cost_per_1k_prompt_tokens=0.003,
            cost_per_1k_completion_tokens=0.015,
            supports_system_prompt=True,
        ),
        "command-r": ModelInfo(
            id="command-r",
            name="Command R",
            context_window=128000,
            max_output_tokens=4096,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
            ],
            cost_per_1k_prompt_tokens=0.0005,
            cost_per_1k_completion_tokens=0.0015,
            supports_system_prompt=True,
        ),
        "command": ModelInfo(
            id="command",
            name="Command",
            context_window=4096,
            max_output_tokens=4096,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
            ],
            cost_per_1k_prompt_tokens=0.0015,
            cost_per_1k_completion_tokens=0.002,
            supports_system_prompt=True,
        ),
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.cohere.ai/v1",
        timeout: int = 300,
    ):
        """
        Initialize Cohere client.

        Args:
            api_key: Cohere API key (or use COHERE_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError("Cohere API key required. Set COHERE_API_KEY env var or pass api_key.")

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
        """Generate completion from Cohere model."""
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model {model} not found")

        # Cohere uses chat format
        # Combine system prompt and messages
        chat_history = []
        if system_prompt:
            chat_history.append({"role": "SYSTEM", "message": system_prompt})

        for msg in messages:
            role = "USER" if msg.role == "user" else "CHATBOT" if msg.role == "assistant" else "SYSTEM"
            chat_history.append({"role": role, "message": msg.content})

        # Last message is the prompt
        prompt = messages[-1].content if messages else ""

        # Prepare request
        request_data = {
            "model": model,
            "message": prompt,
            "chat_history": chat_history[:-1] if len(chat_history) > 1 else [],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            request_data["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameter_definitions": tool.parameters,
                }
                for tool in tools
            ]

        if stop_sequences:
            request_data["stop_sequences"] = stop_sequences

        try:
            response = await self.client.post("/chat", json=request_data)
            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data.get("text", "")
            tool_calls = None

            # Extract tool calls if present
            if "tool_calls" in data:
                tool_calls = [
                    ToolCall(
                        id=f"cohere-{i}",
                        name=tc["name"],
                        arguments=tc.get("parameters", {}),
                    )
                    for i, tc in enumerate(data["tool_calls"])
                ]

            # Extract usage
            usage = Usage(
                prompt_tokens=data.get("meta", {}).get("tokens", {}).get("input_tokens", 0),
                completion_tokens=data.get("meta", {}).get("tokens", {}).get("output_tokens", 0),
                total_tokens=data.get("meta", {}).get("tokens", {}).get("total_tokens", 0),
            )

            return Completion(
                id=data.get("generation_id", "unknown"),
                content=content,
                model=model,
                usage=usage,
                finish_reason=data.get("finish_reason", "stop"),
                tool_calls=tool_calls,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid Cohere API key")
            elif e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                raise RateLimitError(retry_after=retry_after)
            elif e.response.status_code == 400:
                raise InvalidRequestError(f"Invalid request: {e.response.text}")
            else:
                raise AIProviderError(f"Cohere API error: {e.response.text}")

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
        """Stream completion from Cohere model."""
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model {model} not found")

        # Prepare chat history (same as complete)
        chat_history = []
        if system_prompt:
            chat_history.append({"role": "SYSTEM", "message": system_prompt})

        for msg in messages[:-1]:
            role = "USER" if msg.role == "user" else "CHATBOT" if msg.role == "assistant" else "SYSTEM"
            chat_history.append({"role": role, "message": msg.content})

        prompt = messages[-1].content if messages else ""

        request_data = {
            "model": model,
            "message": prompt,
            "chat_history": chat_history,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if tools:
            request_data["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameter_definitions": tool.parameters,
                }
                for tool in tools
            ]

        try:
            async with self.client.stream("POST", "/chat", json=request_data) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            if "text" in data:
                                yield StreamChunk(content=data["text"])

                            if "finish_reason" in data:
                                yield StreamChunk(
                                    content="",
                                    finish_reason=data["finish_reason"],
                                )
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid Cohere API key")
            elif e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                raise RateLimitError(retry_after=retry_after)
            else:
                raise AIProviderError(f"Cohere API error: {e.response.text}")

    def list_models(self) -> List[ModelInfo]:
        """List available Cohere models."""
        return list(self.MODELS.values())

    async def health_check(self) -> bool:
        """Check if Cohere API is healthy."""
        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

