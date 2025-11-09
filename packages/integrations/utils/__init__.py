"""
AI Provider Utilities

Utilities for token counting, prompt compression, rate limiting, and retry handling.
"""

from .token_counter import (
    TokenCounter,
    TokenCounterResult,
    UnsupportedTokenizerError,
    count_tokens,
    count_tokens_with_details,
    count_messages_tokens,
    estimate_cost,
    fits_context_window,
)

from .prompt_compressor import (
    PromptCompressor,
    compress,
    compress_messages,
    calculate_savings,
)

from .rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimiterRegistry,
    get_limiter,
    get_all_usage,
)

from .retry_handler import (
    RetryHandler,
    RetryConfig,
    CircuitBreaker,
    CircuitBreakerError,
    with_retry,
    retry,
)

__all__ = [
    # Token counter
    "TokenCounter",
    "TokenCounterResult",
    "UnsupportedTokenizerError",
    "count_tokens",
    "count_tokens_with_details",
    "count_messages_tokens",
    "estimate_cost",
    "fits_context_window",
    # Prompt compressor
    "PromptCompressor",
    "compress",
    "compress_messages",
    "calculate_savings",
    # Rate limiter
    "RateLimiter",
    "RateLimitConfig",
    "RateLimiterRegistry",
    "get_limiter",
    "get_all_usage",
    # Retry handler
    "RetryHandler",
    "RetryConfig",
    "CircuitBreaker",
    "CircuitBreakerError",
    "with_retry",
    "retry",
]
