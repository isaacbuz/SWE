"""
Base AI Provider Interface

Defines the common protocol that all AI provider implementations must follow.
Ensures consistency across different providers (Anthropic, OpenAI, Google, IBM, Local).
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional, Any, Protocol
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ModelCapability(Enum):
    """Capabilities supported by AI models."""
    TEXT_COMPLETION = "text_completion"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    PROMPT_CACHING = "prompt_caching"
    JSON_MODE = "json_mode"
    SUB_AGENTS = "sub_agents"
    CODE_EXECUTION = "code_execution"


@dataclass
class Tool:
    """Function/tool definition for function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = None


@dataclass
class ToolCall:
    """Represents a tool/function call made by the model."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class Message:
    """Represents a message in the conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


@dataclass
class Usage:
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cache_creation_tokens: Optional[int] = None
    cache_read_tokens: Optional[int] = None


@dataclass
class Completion:
    """Represents a completed model response."""
    id: str
    content: str
    model: str
    usage: Usage
    finish_reason: str  # 'stop', 'length', 'tool_calls', 'content_filter'
    tool_calls: Optional[List[ToolCall]] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class StreamChunk:
    """Represents a streaming response chunk."""
    content: str
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


@dataclass
class ModelInfo:
    """Information about a specific model."""
    id: str
    name: str
    context_window: int
    max_output_tokens: int
    capabilities: List[ModelCapability]
    cost_per_1k_prompt_tokens: float
    cost_per_1k_completion_tokens: float
    supports_system_prompt: bool = True


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class RateLimitError(AIProviderError):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s" if retry_after else "Rate limit exceeded")


class AuthenticationError(AIProviderError):
    """Raised when authentication fails."""
    pass


class InvalidRequestError(AIProviderError):
    """Raised when the request is invalid."""
    pass


class ModelNotFoundError(AIProviderError):
    """Raised when the requested model is not found."""
    pass


class AIProvider(ABC):
    """
    Abstract base class for AI provider implementations.

    All provider clients (Anthropic, OpenAI, Google, IBM, Local) must implement this interface.
    """

    @abstractmethod
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
        Generate a completion from the AI model.

        Args:
            messages: List of conversation messages
            model: Model identifier
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            tools: Optional list of tools/functions the model can call
            system_prompt: Optional system prompt
            json_mode: Whether to force JSON output
            stop_sequences: Optional list of sequences that stop generation
            **kwargs: Provider-specific additional parameters

        Returns:
            Completion object with response and metadata

        Raises:
            RateLimitError: When rate limit is exceeded
            AuthenticationError: When authentication fails
            InvalidRequestError: When request is invalid
            ModelNotFoundError: When model is not found
        """
        pass

    @abstractmethod
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
        Generate a streaming completion from the AI model.

        Args:
            messages: List of conversation messages
            model: Model identifier
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            tools: Optional list of tools/functions the model can call
            system_prompt: Optional system prompt
            **kwargs: Provider-specific additional parameters

        Yields:
            StreamChunk objects with incremental response content

        Raises:
            Same exceptions as complete()
        """
        pass

    @abstractmethod
    async def count_tokens(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Tool]] = None
    ) -> int:
        """
        Count tokens for a given input.

        Args:
            messages: List of conversation messages
            model: Model identifier
            tools: Optional list of tools

        Returns:
            Total number of tokens
        """
        pass

    @abstractmethod
    def get_model_info(self, model: str) -> ModelInfo:
        """
        Get information about a specific model.

        Args:
            model: Model identifier

        Returns:
            ModelInfo object with model details

        Raises:
            ModelNotFoundError: When model is not found
        """
        pass

    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """
        List all available models for this provider.

        Returns:
            List of ModelInfo objects
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is available and healthy.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass


class ProviderRegistry:
    """Registry for managing multiple AI providers."""

    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}

    def register(self, name: str, provider: AIProvider) -> None:
        """Register a provider."""
        self._providers[name] = provider

    def get(self, name: str) -> AIProvider:
        """Get a provider by name."""
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not found")
        return self._providers[name]

    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    async def get_available_models(self) -> Dict[str, List[ModelInfo]]:
        """Get all available models from all providers."""
        result = {}
        for name, provider in self._providers.items():
            result[name] = provider.list_models()
        return result
