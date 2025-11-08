"""
Rate Limiter Utility

Implements per-provider rate limiting to prevent hitting API limits
and ensure fair resource usage across multiple requests.
"""

import time
import asyncio
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a provider."""
    requests_per_minute: int
    requests_per_hour: int
    tokens_per_minute: int
    max_concurrent_requests: int = 10


class RateLimiter:
    """
    Per-provider rate limiter with token bucket algorithm.

    Features:
    - Requests per minute/hour limits
    - Token-based rate limiting
    - Concurrent request limits
    - Automatic backoff
    - Fair queuing
    """

    # Default rate limits for different providers
    DEFAULT_LIMITS = {
        "anthropic": RateLimitConfig(
            requests_per_minute=50,
            requests_per_hour=1000,
            tokens_per_minute=40000,
            max_concurrent_requests=5,
        ),
        "openai": RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=3000,
            tokens_per_minute=90000,
            max_concurrent_requests=10,
        ),
        "google": RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            tokens_per_minute=32000,
            max_concurrent_requests=5,
        ),
        "ibm": RateLimitConfig(
            requests_per_minute=30,
            requests_per_hour=500,
            tokens_per_minute=20000,
            max_concurrent_requests=5,
        ),
        "local": RateLimitConfig(
            requests_per_minute=1000,  # No real limits for local
            requests_per_hour=10000,
            tokens_per_minute=1000000,
            max_concurrent_requests=5,  # Limit based on hardware
        ),
    }

    def __init__(self, provider: str, custom_config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            provider: Provider name
            custom_config: Optional custom rate limit configuration
        """
        self.provider = provider
        self.config = custom_config or self.DEFAULT_LIMITS.get(
            provider,
            RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                tokens_per_minute=50000,
                max_concurrent_requests=5,
            )
        )

        # Request tracking
        self.request_times_minute: deque = deque()
        self.request_times_hour: deque = deque()

        # Token tracking
        self.token_times: deque = deque()  # (timestamp, token_count)
        self.current_token_count = 0

        # Concurrent request tracking
        self.current_requests = 0
        self.request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)

        # Lock for thread-safe operations
        self.lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 0) -> None:
        """
        Acquire permission to make a request.

        Blocks until rate limits allow the request.

        Args:
            estimated_tokens: Estimated tokens for this request
        """
        async with self.lock:
            # Wait for concurrent request limit
            await self.request_semaphore.acquire()

            try:
                # Wait for rate limits
                await self._wait_for_request_limit()
                await self._wait_for_token_limit(estimated_tokens)

                # Record request
                now = time.time()
                self.request_times_minute.append(now)
                self.request_times_hour.append(now)

                if estimated_tokens > 0:
                    self.token_times.append((now, estimated_tokens))
                    self.current_token_count += estimated_tokens

                self.current_requests += 1

            except Exception as e:
                # Release semaphore if acquisition fails
                self.request_semaphore.release()
                raise e

    async def release(self) -> None:
        """Release a request slot."""
        async with self.lock:
            self.current_requests = max(0, self.current_requests - 1)
            self.request_semaphore.release()

    async def _wait_for_request_limit(self) -> None:
        """Wait until request rate limits allow a new request."""
        now = time.time()

        # Clean old requests (older than 1 minute)
        while self.request_times_minute and now - self.request_times_minute[0] > 60:
            self.request_times_minute.popleft()

        # Clean old requests (older than 1 hour)
        while self.request_times_hour and now - self.request_times_hour[0] > 3600:
            self.request_times_hour.popleft()

        # Check minute limit
        if len(self.request_times_minute) >= self.config.requests_per_minute:
            # Calculate wait time
            oldest_request = self.request_times_minute[0]
            wait_time = 60 - (now - oldest_request)

            if wait_time > 0:
                logger.info(
                    f"Rate limit (requests/minute) reached for {self.provider}, "
                    f"waiting {wait_time:.2f}s"
                )
                await asyncio.sleep(wait_time)
                return await self._wait_for_request_limit()

        # Check hour limit
        if len(self.request_times_hour) >= self.config.requests_per_hour:
            oldest_request = self.request_times_hour[0]
            wait_time = 3600 - (now - oldest_request)

            if wait_time > 0:
                logger.info(
                    f"Rate limit (requests/hour) reached for {self.provider}, "
                    f"waiting {wait_time:.2f}s"
                )
                await asyncio.sleep(wait_time)
                return await self._wait_for_request_limit()

    async def _wait_for_token_limit(self, tokens: int) -> None:
        """Wait until token rate limits allow a new request."""
        if tokens == 0:
            return

        now = time.time()

        # Clean old token records (older than 1 minute)
        while self.token_times and now - self.token_times[0][0] > 60:
            _, old_tokens = self.token_times.popleft()
            self.current_token_count -= old_tokens

        # Check token limit
        if self.current_token_count + tokens > self.config.tokens_per_minute:
            # Calculate wait time based on oldest tokens
            if self.token_times:
                oldest_time, _ = self.token_times[0]
                wait_time = 60 - (now - oldest_time)

                if wait_time > 0:
                    logger.info(
                        f"Rate limit (tokens/minute) reached for {self.provider}, "
                        f"waiting {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)
                    return await self._wait_for_token_limit(tokens)

    def get_current_usage(self) -> Dict[str, any]:
        """
        Get current rate limit usage.

        Returns:
            Dictionary with current usage statistics
        """
        now = time.time()

        # Clean old records
        while self.request_times_minute and now - self.request_times_minute[0] > 60:
            self.request_times_minute.popleft()

        while self.request_times_hour and now - self.request_times_hour[0] > 3600:
            self.request_times_hour.popleft()

        while self.token_times and now - self.token_times[0][0] > 60:
            _, old_tokens = self.token_times.popleft()
            self.current_token_count -= old_tokens

        return {
            "provider": self.provider,
            "requests_per_minute": {
                "used": len(self.request_times_minute),
                "limit": self.config.requests_per_minute,
                "remaining": max(0, self.config.requests_per_minute - len(self.request_times_minute)),
            },
            "requests_per_hour": {
                "used": len(self.request_times_hour),
                "limit": self.config.requests_per_hour,
                "remaining": max(0, self.config.requests_per_hour - len(self.request_times_hour)),
            },
            "tokens_per_minute": {
                "used": self.current_token_count,
                "limit": self.config.tokens_per_minute,
                "remaining": max(0, self.config.tokens_per_minute - self.current_token_count),
            },
            "concurrent_requests": {
                "active": self.current_requests,
                "limit": self.config.max_concurrent_requests,
            },
        }

    async def __aenter__(self):
        """Context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.release()


class RateLimiterRegistry:
    """Registry for managing rate limiters for multiple providers."""

    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}

    def get_limiter(
        self,
        provider: str,
        custom_config: Optional[RateLimitConfig] = None
    ) -> RateLimiter:
        """
        Get or create a rate limiter for a provider.

        Args:
            provider: Provider name
            custom_config: Optional custom configuration

        Returns:
            RateLimiter instance
        """
        if provider not in self._limiters:
            self._limiters[provider] = RateLimiter(provider, custom_config)

        return self._limiters[provider]

    def get_all_usage(self) -> Dict[str, Dict]:
        """Get usage statistics for all providers."""
        return {
            provider: limiter.get_current_usage()
            for provider, limiter in self._limiters.items()
        }


# Global registry
_registry = RateLimiterRegistry()


# Convenience functions
def get_limiter(
    provider: str,
    custom_config: Optional[RateLimitConfig] = None
) -> RateLimiter:
    """Get a rate limiter for a provider."""
    return _registry.get_limiter(provider, custom_config)


def get_all_usage() -> Dict[str, Dict]:
    """Get usage statistics for all providers."""
    return _registry.get_all_usage()
