"""
AI Provider Integrations Package

Unified interface for multiple AI providers with advanced features.
"""

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
    ProviderRegistry,
    # Exceptions
    AIProviderError,
    RateLimitError,
    AuthenticationError,
    InvalidRequestError,
    ModelNotFoundError,
)

from .anthropic_client import AnthropicClient
from .openai_client import OpenAIClient
from .google_client import GoogleClient
from .ibm_client import IBMClient
from .local_client import LocalClient

__version__ = "1.0.0"

__all__ = [
    # Base classes
    "AIProvider",
    "Completion",
    "StreamChunk",
    "Message",
    "Tool",
    "ToolCall",
    "Usage",
    "ModelInfo",
    "ModelCapability",
    "ProviderRegistry",
    # Exceptions
    "AIProviderError",
    "RateLimitError",
    "AuthenticationError",
    "InvalidRequestError",
    "ModelNotFoundError",
    # Clients
    "AnthropicClient",
    "OpenAIClient",
    "GoogleClient",
    "IBMClient",
    "LocalClient",
]
