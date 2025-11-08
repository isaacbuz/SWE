"""
Google Gemini Integration

Implements the AIProvider interface for Google's Gemini models.
Supports Gemini Pro, Ultra with multimodal capabilities,
function calling, and streaming.
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


class GoogleClient(AIProvider):
    """
    Google Gemini API client.

    Features:
    - Gemini Pro, Flash, Ultra models
    - Multimodal support (text, images, video, audio)
    - Function calling
    - Streaming support
    - Long context windows
    """

    # Model catalog
    MODELS = {
        "gemini-1.5-pro": ModelInfo(
            id="gemini-1.5-pro",
            name="Gemini 1.5 Pro",
            context_window=2000000,  # 2M tokens
            max_output_tokens=8192,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
            ],
            cost_per_1k_prompt_tokens=0.00125,
            cost_per_1k_completion_tokens=0.005,
            supports_system_prompt=True,
        ),
        "gemini-1.5-flash": ModelInfo(
            id="gemini-1.5-flash",
            name="Gemini 1.5 Flash",
            context_window=1000000,  # 1M tokens
            max_output_tokens=8192,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
            ],
            cost_per_1k_prompt_tokens=0.000075,
            cost_per_1k_completion_tokens=0.0003,
            supports_system_prompt=True,
        ),
        "gemini-pro": ModelInfo(
            id="gemini-pro",
            name="Gemini Pro",
            context_window=32768,
            max_output_tokens=8192,
            capabilities=[
                ModelCapability.TEXT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING,
            ],
            cost_per_1k_prompt_tokens=0.0005,
            cost_per_1k_completion_tokens=0.0015,
            supports_system_prompt=True,
        ),
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout: float = 300.0,
        max_retries: int = 3,
    ):
        """
        Initialize Google Gemini client.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
        )

    def _format_messages(self, messages: List[Message]) -> Dict[str, Any]:
        """Convert Message objects to Gemini API format."""
        contents = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
                continue

            # Map roles to Gemini format
            role = "user" if msg.role == "user" else "model"

            parts = []
            if msg.content:
                parts.append({"text": msg.content})

            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    parts.append({
                        "functionCall": {
                            "name": tool_call.name,
                            "args": tool_call.arguments,
                        }
                    })

            if msg.tool_call_id:
                parts.append({
                    "functionResponse": {
                        "name": msg.tool_call_id,
                        "response": {"result": msg.content},
                    }
                })

            contents.append({"role": role, "parts": parts})

        result = {"contents": contents}
        if system_instruction:
            result["system_instruction"] = {"parts": [{"text": system_instruction}]}

        return result

    def _format_tools(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Convert Tool objects to Gemini API format."""
        function_declarations = []

        for tool in tools:
            function_declarations.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": tool.required or [],
                },
            })

        return [{"function_declarations": function_declarations}]

    def _parse_response(self, response: Dict[str, Any], model: str) -> Completion:
        """Parse Gemini API response into Completion object."""
        candidate = response["candidates"][0]
        content_part = candidate.get("content", {})

        content = ""
        tool_calls = []

        for part in content_part.get("parts", []):
            if "text" in part:
                content += part["text"]
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(
                    ToolCall(
                        id=fc.get("name", ""),
                        name=fc["name"],
                        arguments=fc.get("args", {}),
                    )
                )

        # Gemini doesn't provide detailed token counts in all responses
        usage_metadata = response.get("usageMetadata", {})
        usage = Usage(
            prompt_tokens=usage_metadata.get("promptTokenCount", 0),
            completion_tokens=usage_metadata.get("candidatesTokenCount", 0),
            total_tokens=usage_metadata.get("totalTokenCount", 0),
        )

        finish_reason_map = {
            "STOP": "stop",
            "MAX_TOKENS": "length",
            "SAFETY": "content_filter",
            "RECITATION": "content_filter",
        }

        finish_reason = candidate.get("finishReason", "STOP")
        finish_reason = finish_reason_map.get(finish_reason, "stop")

        return Completion(
            id=response.get("modelVersion", ""),
            content=content,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
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
        **kwargs
    ) -> Completion:
        """
        Generate a completion using Gemini.

        Args:
            messages: Conversation messages
            model: Model ID (e.g., 'gemini-1.5-pro')
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            tools: Optional tools for function calling
            system_prompt: Optional system prompt
            json_mode: Force JSON output
            stop_sequences: Optional stop sequences
            **kwargs: Additional Gemini-specific parameters

        Returns:
            Completion object
        """
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")

        # Add system prompt to messages if provided
        if system_prompt:
            messages = [Message(role="system", content=system_prompt)] + messages

        # Format messages
        request_body = self._format_messages(messages)

        # Generation config
        generation_config = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        if stop_sequences:
            generation_config["stopSequences"] = stop_sequences

        request_body["generationConfig"] = generation_config

        # Add tools if provided
        if tools:
            request_body["tools"] = self._format_tools(tools)

        # Add any additional kwargs
        request_body.update(kwargs)

        # Make API request with retries
        endpoint = f"/models/{model}:generateContent"
        url = f"{endpoint}?key={self.api_key}"

        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(url, json=request_body)

                if response.status_code == 200:
                    return self._parse_response(response.json(), model)
                elif response.status_code == 429:
                    raise RateLimitError()
                elif response.status_code == 401 or response.status_code == 403:
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
        Generate a streaming completion using Gemini.

        Yields:
            StreamChunk objects with incremental content
        """
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")

        # Add system prompt to messages if provided
        if system_prompt:
            messages = [Message(role="system", content=system_prompt)] + messages

        # Format messages
        request_body = self._format_messages(messages)

        # Generation config
        generation_config = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        request_body["generationConfig"] = generation_config

        # Add tools if provided
        if tools:
            request_body["tools"] = self._format_tools(tools)

        request_body.update(kwargs)

        # Make streaming request
        endpoint = f"/models/{model}:streamGenerateContent"
        url = f"{endpoint}?key={self.api_key}&alt=sse"

        async with self.client.stream("POST", url, json=request_body) as response:
            if response.status_code != 200:
                if response.status_code == 429:
                    raise RateLimitError()
                elif response.status_code == 401 or response.status_code == 403:
                    raise AuthenticationError("Invalid API key")
                else:
                    response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip() or not line.startswith("data: "):
                    continue

                data = line[6:]  # Remove "data: " prefix

                try:
                    chunk_data = json.loads(data)

                    if "candidates" in chunk_data:
                        candidate = chunk_data["candidates"][0]
                        content_part = candidate.get("content", {})

                        for part in content_part.get("parts", []):
                            if "text" in part:
                                yield StreamChunk(content=part["text"])

                        finish_reason = candidate.get("finishReason")
                        if finish_reason:
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
        Count tokens using Gemini's countTokens endpoint.
        """
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")

        request_body = self._format_messages(messages)

        if tools:
            request_body["tools"] = self._format_tools(tools)

        endpoint = f"/models/{model}:countTokens"
        url = f"{endpoint}?key={self.api_key}"

        try:
            response = await self.client.post(url, json=request_body)
            if response.status_code == 200:
                data = response.json()
                return data.get("totalTokens", 0)
            else:
                # Fallback to approximation
                total_chars = sum(len(m.content) for m in messages if m.content)
                return total_chars // 4
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using approximation")
            total_chars = sum(len(m.content) for m in messages if m.content)
            return total_chars // 4

    def get_model_info(self, model: str) -> ModelInfo:
        """Get information about a specific Gemini model."""
        if model not in self.MODELS:
            raise ModelNotFoundError(f"Model '{model}' not found")
        return self.MODELS[model]

    def list_models(self) -> List[ModelInfo]:
        """List all available Gemini models."""
        return list(self.MODELS.values())

    async def health_check(self) -> bool:
        """Check if Google Gemini API is available."""
        try:
            # List models as a simple health check
            url = f"/models?key={self.api_key}"
            response = await self.client.get(url)
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
