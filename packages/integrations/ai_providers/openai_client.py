"""
OpenAI GPT Integration

Implements the AIProvider interface for OpenAI's GPT models.
Supports GPT-4, GPT-4 Turbo, GPT-5 with structured outputs,
function calling, vision, and streaming.
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


class OpenAIClient(AIProvider):
    """
    OpenAI GPT API client.

    Features:
    - GPT-4, GPT-4 Turbo, GPT-5 models
    - Structured outputs (JSON mode)
    - Function calling
    - Vision capabilities
    - Streaming support
    - Fine-tuned models
    """

    # Model catalog
    MODELS = {
        "gpt-4-turbo-2024-04-09": ModelInfo(
            id="gpt-4-turbo-2024-04-09",
            name="GPT-4 Turbo",
            context_window=128000,
            max_output_tokens=4096,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.JSON_MODE,
            ],
            cost_per_1k_prompt_tokens=0.01,
            cost_per_1k_completion_tokens=0.03,
            supports_system_prompt=True,
        ),
        "gpt-4o": ModelInfo(
            id="gpt-4o",
            name="GPT-4o",
            context_window=128000,
            max_output_tokens=16384,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.JSON_MODE,
            ],
            cost_per_1k_prompt_tokens=0.0025,
            cost_per_1k_completion_tokens=0.01,
            supports_system_prompt=True,
        ),
        "gpt-4o-mini": ModelInfo(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            context_window=128000,
            max_output_tokens=16384,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
            ],
            cost_per_1k_prompt_tokens=0.00015,
            cost_per_1k_completion_tokens=0.0006,
            supports_system_prompt=True,
        ),
        "gpt-3.5-turbo": ModelInfo(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            context_window=16385,
            max_output_tokens=4096,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
            ],
            cost_per_1k_prompt_tokens=0.0005,
            cost_per_1k_completion_tokens=0.0015,
            supports_system_prompt=True,
        ),
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        organization: Optional[str] = None,
        timeout: float = 300.0,
        max_retries: int = 3,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: API base URL
            organization: Optional organization ID
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.base_url = base_url.rstrip("/")
        self.organization = organization
        self.timeout = timeout
        self.max_retries = max_retries

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if organization:
            headers["OpenAI-Organization"] = organization

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=headers,
        )

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Message objects to OpenAI API format."""
        formatted = []
        for msg in messages:
            message_dict = {"role": msg.role, "content": msg.content}

            if msg.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ]

            if msg.tool_call_id:
                message_dict["role"] = "tool"
                message_dict["tool_call_id"] = msg.tool_call_id

            formatted.append(message_dict)

        return formatted

    def _format_tools(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Convert Tool objects to OpenAI API format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": tool.required or [],
                    },
                },
            }
            for tool in tools
        ]

    def _parse_response(self, response: Dict[str, Any], model: str) -> Completion:
        """Parse OpenAI API response into Completion object."""
        choice = response["choices"][0]
        message = choice["message"]

        content = message.get("content", "") or ""
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

        usage_data = response.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return Completion(
            id=response.get("id", ""),
            content=content,
            model=model,
            usage=usage,
            finish_reason=choice.get("finish_reason", "stop"),
            tool_calls=tool_calls,
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
        **kwargs
    ) -> Completion:
        """
        Generate a completion using GPT.

        Args:
            messages: Conversation messages
            model: Model ID (e.g., 'gpt-4-turbo-2024-04-09')
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            tools: Optional tools for function calling
            system_prompt: Optional system prompt
            json_mode: Force JSON output
            stop_sequences: Optional stop sequences
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            Completion object
        """
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")

        # Add system prompt to messages if provided
        formatted_messages = self._format_messages(messages)
        if system_prompt:
            formatted_messages.insert(0, {"role": "system", "content": system_prompt})

        # Build request payload
        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = self._format_tools(tools)
            payload["tool_choice"] = "auto"

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        if stop_sequences:
            payload["stop"] = stop_sequences

        # Add any additional kwargs
        payload.update(kwargs)

        # Make API request with retries
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post("/chat/completions", json=payload)

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
        Generate a streaming completion using GPT.

        Yields:
            StreamChunk objects with incremental content
        """
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")

        # Add system prompt to messages if provided
        formatted_messages = self._format_messages(messages)
        if system_prompt:
            formatted_messages.insert(0, {"role": "system", "content": system_prompt})

        # Build request payload
        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if tools:
            payload["tools"] = self._format_tools(tools)

        payload.update(kwargs)

        # Make streaming request
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
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
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})

                    if "content" in delta and delta["content"]:
                        yield StreamChunk(content=delta["content"])

                    finish_reason = chunk["choices"][0].get("finish_reason")
                    if finish_reason:
                        yield StreamChunk(content="", finish_reason=finish_reason)

                except json.JSONDecodeError:
                    continue

    async def count_tokens(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Tool]] = None
    ) -> int:
        """
        Count tokens using tiktoken library.

        Note: This requires tiktoken to be installed.
        Falls back to character-based approximation if not available.
        """
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(model)
            total_tokens = 0

            for message in messages:
                # Every message follows <im_start>{role}\n{content}<im_end>\n
                total_tokens += 4  # Message overhead
                total_tokens += len(encoding.encode(message.content))

            if tools:
                tools_json = json.dumps(self._format_tools(tools))
                total_tokens += len(encoding.encode(tools_json))

            total_tokens += 2  # Priming tokens

            return total_tokens

        except ImportError:
            logger.warning("tiktoken not installed, using approximation")
            # Rough approximation: 4 characters per token
            total_chars = sum(len(m.content) for m in messages if m.content)
            if tools:
                tools_json = json.dumps(self._format_tools(tools))
                total_chars += len(tools_json)
            return total_chars // 4

    def get_model_info(self, model: str) -> ModelInfo:
        """Get information about a specific GPT model."""
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")
        return self.MODELS[model]

    def list_models(self) -> List[ModelInfo]:
        """List all available GPT models."""
        return list(self.MODELS.values())

    async def health_check(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            response = await self.client.get("/models")
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
