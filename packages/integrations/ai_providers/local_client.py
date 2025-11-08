"""
Local Models Integration

Implements the AIProvider interface for locally-hosted models.
Supports Ollama and vLLM for running models on-premises,
useful for sensitive data that cannot leave infrastructure.
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


class LocalClient(AIProvider):
    """
    Local models API client supporting Ollama and vLLM.

    Features:
    - Run models locally for data privacy
    - Support for Ollama (easy setup)
    - Support for vLLM (high performance)
    - No external API dependencies
    - Cost-free inference
    """

    def __init__(
        self,
        backend: str = "ollama",  # "ollama" or "vllm"
        base_url: Optional[str] = None,
        timeout: float = 300.0,
        max_retries: int = 3,
    ):
        """
        Initialize local model client.

        Args:
            backend: Backend type ("ollama" or "vllm")
            base_url: API base URL (defaults based on backend)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.backend = backend.lower()

        if self.backend not in ["ollama", "vllm"]:
            raise ValueError("Backend must be 'ollama' or 'vllm'")

        # Set default URLs based on backend
        if base_url is None:
            if self.backend == "ollama":
                base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            else:  # vllm
                base_url = os.getenv("VLLM_HOST", "http://localhost:8000")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
        )

        # Cache for available models
        self._models_cache: Optional[List[ModelInfo]] = None

    def _format_messages_ollama(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Message objects to Ollama API format."""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content,
            })
        return formatted

    def _format_messages_vllm(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Message objects to vLLM (OpenAI-compatible) format."""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content,
            })
        return formatted

    async def _list_ollama_models(self) -> List[ModelInfo]:
        """List available models from Ollama."""
        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = []

                for model_data in data.get("models", []):
                    name = model_data.get("name", "")
                    size = model_data.get("size", 0)

                    # Estimate context window based on model name
                    context_window = 4096  # Default
                    if "32k" in name:
                        context_window = 32768
                    elif "16k" in name:
                        context_window = 16384
                    elif "8k" in name:
                        context_window = 8192

                    models.append(ModelInfo(
                        id=name,
                        name=name,
                        context_window=context_window,
                        max_output_tokens=2048,
                        capabilities=[
                            ModelCapability.TEXT_COMPLETION,
                            ModelCapability.STREAMING,
                        ],
                        cost_per_1k_prompt_tokens=0.0,  # Local = free
                        cost_per_1k_completion_tokens=0.0,
                        supports_system_prompt=True,
                    ))

                return models
            else:
                logger.warning("Failed to list Ollama models")
                return []
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

    async def _list_vllm_models(self) -> List[ModelInfo]:
        """List available models from vLLM."""
        try:
            response = await self.client.get("/v1/models")
            if response.status_code == 200:
                data = response.json()
                models = []

                for model_data in data.get("data", []):
                    name = model_data.get("id", "")

                    models.append(ModelInfo(
                        id=name,
                        name=name,
                        context_window=4096,  # Default, can be configured per model
                        max_output_tokens=2048,
                        capabilities=[
                            ModelCapability.TEXT_COMPLETION,
                            ModelCapability.STREAMING,
                        ],
                        cost_per_1k_prompt_tokens=0.0,
                        cost_per_1k_completion_tokens=0.0,
                        supports_system_prompt=True,
                    ))

                return models
            else:
                logger.warning("Failed to list vLLM models")
                return []
        except Exception as e:
            logger.error(f"Error listing vLLM models: {e}")
            return []

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
        Generate a completion using local model.

        Args:
            messages: Conversation messages
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional tools (limited support)
            system_prompt: Optional system prompt
            json_mode: Force JSON output (via prompt)
            stop_sequences: Optional stop sequences
            **kwargs: Additional backend-specific parameters

        Returns:
            Completion object
        """
        if tools:
            logger.warning("Local models have limited function calling support")

        # Add system prompt to messages if provided
        if system_prompt:
            messages = [Message(role="system", content=system_prompt)] + messages

        if self.backend == "ollama":
            return await self._complete_ollama(
                messages, model, temperature, max_tokens, stop_sequences, json_mode, **kwargs
            )
        else:  # vllm
            return await self._complete_vllm(
                messages, model, temperature, max_tokens, stop_sequences, json_mode, **kwargs
            )

    async def _complete_ollama(
        self,
        messages: List[Message],
        model: str,
        temperature: float,
        max_tokens: int,
        stop_sequences: Optional[List[str]],
        json_mode: bool,
        **kwargs
    ) -> Completion:
        """Complete using Ollama backend."""
        payload = {
            "model": model,
            "messages": self._format_messages_ollama(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        if stop_sequences:
            payload["options"]["stop"] = stop_sequences

        if json_mode:
            payload["format"] = "json"

        payload["options"].update(kwargs)

        for attempt in range(self.max_retries):
            try:
                response = await self.client.post("/api/chat", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    message = data.get("message", {})
                    content = message.get("content", "")

                    # Ollama provides token counts in some cases
                    eval_count = data.get("eval_count", 0)
                    prompt_eval_count = data.get("prompt_eval_count", 0)

                    usage = Usage(
                        prompt_tokens=prompt_eval_count,
                        completion_tokens=eval_count,
                        total_tokens=prompt_eval_count + eval_count,
                    )

                    return Completion(
                        id=model,
                        content=content,
                        model=model,
                        usage=usage,
                        finish_reason="stop",
                    )
                elif response.status_code == 404:
                    raise ModelNotFoundError(f"Model '{model}' not found. Try pulling it with 'ollama pull {model}'")
                else:
                    response.raise_for_status()

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt == self.max_retries - 1:
                    raise AIProviderError(f"Network error after {self.max_retries} attempts: {e}")
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                continue

        raise AIProviderError("Max retries exceeded")

    async def _complete_vllm(
        self,
        messages: List[Message],
        model: str,
        temperature: float,
        max_tokens: int,
        stop_sequences: Optional[List[str]],
        json_mode: bool,
        **kwargs
    ) -> Completion:
        """Complete using vLLM backend (OpenAI-compatible API)."""
        payload = {
            "model": model,
            "messages": self._format_messages_vllm(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if stop_sequences:
            payload["stop"] = stop_sequences

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        payload.update(kwargs)

        for attempt in range(self.max_retries):
            try:
                response = await self.client.post("/v1/chat/completions", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    choice = data["choices"][0]
                    message = choice["message"]
                    content = message.get("content", "")

                    usage_data = data.get("usage", {})
                    usage = Usage(
                        prompt_tokens=usage_data.get("prompt_tokens", 0),
                        completion_tokens=usage_data.get("completion_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0),
                    )

                    return Completion(
                        id=data.get("id", ""),
                        content=content,
                        model=model,
                        usage=usage,
                        finish_reason=choice.get("finish_reason", "stop"),
                    )
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
        Generate a streaming completion using local model.

        Yields:
            StreamChunk objects with incremental content
        """
        # Add system prompt to messages if provided
        if system_prompt:
            messages = [Message(role="system", content=system_prompt)] + messages

        if self.backend == "ollama":
            async for chunk in self._stream_ollama(messages, model, temperature, max_tokens, **kwargs):
                yield chunk
        else:  # vllm
            async for chunk in self._stream_vllm(messages, model, temperature, max_tokens, **kwargs):
                yield chunk

    async def _stream_ollama(
        self,
        messages: List[Message],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream using Ollama backend."""
        payload = {
            "model": model,
            "messages": self._format_messages_ollama(messages),
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        payload["options"].update(kwargs)

        async with self.client.stream("POST", "/api/chat", json=payload) as response:
            if response.status_code != 200:
                response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)
                    message = data.get("message", {})
                    content = message.get("content", "")

                    if content:
                        yield StreamChunk(content=content)

                    if data.get("done", False):
                        yield StreamChunk(content="", finish_reason="stop")

                except json.JSONDecodeError:
                    continue

    async def _stream_vllm(
        self,
        messages: List[Message],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream using vLLM backend."""
        payload = {
            "model": model,
            "messages": self._format_messages_vllm(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        payload.update(kwargs)

        async with self.client.stream("POST", "/v1/chat/completions", json=payload) as response:
            if response.status_code != 200:
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
        Count tokens (approximation for local models).

        Local models don't typically provide tokenization endpoints,
        so we use character-based approximation.
        """
        total_chars = sum(len(m.content) for m in messages if m.content)
        # Rough approximation: 4 characters per token
        return total_chars // 4

    def get_model_info(self, model: str) -> ModelInfo:
        """Get information about a specific local model."""
        # For local models, we need to query the backend
        if self._models_cache is None:
            raise AIProviderError("Models not loaded. Call list_models() first.")

        for model_info in self._models_cache:
            if model_info.id == model:
                return model_info

        raise ModelNotFoundError(f"Model '{model}' not found")

    def list_models(self) -> List[ModelInfo]:
        """List all available local models."""
        # This needs to be called asynchronously, so we can't implement it synchronously
        # Return cached models if available
        if self._models_cache is not None:
            return self._models_cache
        return []

    async def refresh_models(self) -> List[ModelInfo]:
        """Refresh the list of available models."""
        if self.backend == "ollama":
            self._models_cache = await self._list_ollama_models()
        else:  # vllm
            self._models_cache = await self._list_vllm_models()

        return self._models_cache

    async def health_check(self) -> bool:
        """Check if local model server is available."""
        try:
            if self.backend == "ollama":
                response = await self.client.get("/api/tags")
            else:  # vllm
                response = await self.client.get("/v1/models")

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
