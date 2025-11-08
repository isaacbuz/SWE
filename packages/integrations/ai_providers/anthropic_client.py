"""
Anthropic Claude Integration

Implements the AIProvider interface for Anthropic's Claude models.
Supports Claude 3.5 Sonnet, Opus, Haiku with advanced features like
prompt caching, tool use, and streaming.
"""

import os
import json
import logging
from typing import AsyncIterator, Dict, List, Optional, Any
from datetime import datetime

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


class AnthropicClient(AIProvider):
    """
    Anthropic Claude API client.

    Features:
    - Claude 3.5 Sonnet, Opus, Haiku models
    - Tool use (function calling)
    - Streaming support
    - Prompt caching for cost reduction
    - Sub-agent capabilities
    - Vision support (image analysis)
    """

    # Model catalog
    MODELS = {
        "claude-3-5-sonnet-20241022": ModelInfo(
            id="claude-3-5-sonnet-20241022",
            name="Claude 3.5 Sonnet",
            context_window=200000,
            max_output_tokens=8192,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.PROMPT_CACHING,
                ModelCapability.SUB_AGENTS,
            ],
            cost_per_1k_prompt_tokens=0.003,
            cost_per_1k_completion_tokens=0.015,
            supports_system_prompt=True,
        ),
        "claude-3-opus-20240229": ModelInfo(
            id="claude-3-opus-20240229",
            name="Claude 3 Opus",
            context_window=200000,
            max_output_tokens=4096,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.PROMPT_CACHING,
            ],
            cost_per_1k_prompt_tokens=0.015,
            cost_per_1k_completion_tokens=0.075,
            supports_system_prompt=True,
        ),
        "claude-3-5-haiku-20241022": ModelInfo(
            id="claude-3-5-haiku-20241022",
            name="Claude 3.5 Haiku",
            context_window=200000,
            max_output_tokens=8192,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.PROMPT_CACHING,
            ],
            cost_per_1k_prompt_tokens=0.001,
            cost_per_1k_completion_tokens=0.005,
            supports_system_prompt=True,
        ),
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.anthropic.com",
        timeout: float = 300.0,
        max_retries: int = 3,
    ):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Message objects to Anthropic API format."""
        formatted = []
        for msg in messages:
            if msg.role == "system":
                continue  # System messages handled separately

            content = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})

            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tool_call.id,
                        "name": tool_call.name,
                        "input": tool_call.arguments,
                    })

            if msg.tool_call_id:
                content = [{
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content,
                }]

            formatted.append({
                "role": "user" if msg.role == "user" else "assistant",
                "content": content,
            })

        return formatted

    def _format_tools(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Convert Tool objects to Anthropic API format."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": tool.required or [],
                },
            }
            for tool in tools
        ]

    def _parse_response(self, response: Dict[str, Any], model: str) -> Completion:
        """Parse Anthropic API response into Completion object."""
        content = ""
        tool_calls = []

        for block in response.get("content", []):
            if block["type"] == "text":
                content += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block["id"],
                        name=block["name"],
                        arguments=block["input"],
                    )
                )

        usage_data = response.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
            cache_creation_tokens=usage_data.get("cache_creation_input_tokens"),
            cache_read_tokens=usage_data.get("cache_read_input_tokens"),
        )

        return Completion(
            id=response.get("id", ""),
            content=content,
            model=model,
            usage=usage,
            finish_reason=response.get("stop_reason", "stop"),
            tool_calls=tool_calls if tool_calls else None,
        )

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
        enable_caching: bool = False,
        **kwargs
    ) -> Completion:
        """
        Generate a completion using Claude.

        Args:
            messages: Conversation messages
            model: Model ID (e.g., 'claude-3-5-sonnet-20241022')
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            tools: Optional tools for function calling
            system_prompt: Optional system prompt
            json_mode: Force JSON output (via system prompt)
            stop_sequences: Optional stop sequences
            enable_caching: Enable prompt caching
            **kwargs: Additional Anthropic-specific parameters

        Returns:
            Completion object
        """
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")

        # Extract system prompt from messages if not provided
        if not system_prompt:
            system_messages = [m for m in messages if m.role == "system"]
            if system_messages:
                system_prompt = "\n".join(m.content for m in system_messages)

        # Add JSON mode instruction to system prompt
        if json_mode and system_prompt:
            system_prompt += "\n\nRespond only with valid JSON."

        # Build request payload
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": self._format_messages(messages),
        }

        if system_prompt:
            # Enable caching for system prompt if requested
            if enable_caching:
                payload["system"] = [
                    {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}
                ]
            else:
                payload["system"] = system_prompt

        if tools:
            payload["tools"] = self._format_tools(tools)

        if stop_sequences:
            payload["stop_sequences"] = stop_sequences

        # Add any additional kwargs
        payload.update(kwargs)

        # Make API request with retries
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post("/v1/messages", json=payload)

                if response.status_code == 200:
                    return self._parse_response(response.json(), model)
                elif response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    raise RateLimitError(int(retry_after) if retry_after else None)
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 400:
                    error_data = response.json()
                    raise InvalidRequestError(error_data.get("error", {}).get("message", "Invalid request"))
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
        Generate a streaming completion using Claude.

        Yields:
            StreamChunk objects with incremental content
        """
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")

        # Extract system prompt from messages if not provided
        if not system_prompt:
            system_messages = [m for m in messages if m.role == "system"]
            if system_messages:
                system_prompt = "\n".join(m.content for m in system_messages)

        # Build request payload
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": self._format_messages(messages),
            "stream": True,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if tools:
            payload["tools"] = self._format_tools(tools)

        payload.update(kwargs)

        # Make streaming request
        async with self.client.stream("POST", "/v1/messages", json=payload) as response:
            if response.status_code != 200:
                if response.status_code == 429:
                    raise RateLimitError()
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                else:
                    response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip() or not line.startswith("data: "):
                    continue

                data = line[6:]  # Remove "data: " prefix
                if data == "[DONE]":
                    break

                try:
                    event = json.loads(data)
                    event_type = event.get("type")

                    if event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield StreamChunk(content=delta.get("text", ""))

                    elif event_type == "message_stop":
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
        Count tokens for input using Claude's counting endpoint.

        Note: Anthropic uses a rough approximation of ~4 chars per token.
        For accurate counting, use the official tokenizer.
        """
        total_chars = sum(len(m.content) for m in messages if m.content)

        if tools:
            tools_json = json.dumps(self._format_tools(tools))
            total_chars += len(tools_json)

        # Rough approximation: 4 characters per token
        return total_chars // 4

    def get_model_info(self, model: str) -> ModelInfo:
        """Get information about a specific Claude model."""
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")
        return self.MODELS[model]

    def list_models(self) -> List[ModelInfo]:
        """List all available Claude models."""
        return list(self.MODELS.values())

    async def health_check(self) -> bool:
        """Check if Anthropic API is available."""
        try:
            # Make a minimal request to check API availability
            response = await self.client.post(
                "/v1/messages",
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                }
            )
            return response.status_code == 200
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
