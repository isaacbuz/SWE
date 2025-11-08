"""
Retry Handler Utility

Implements exponential backoff with jitter for handling transient
failures and rate limit errors when calling AI provider APIs.
"""

import asyncio
import random
import logging
from typing import Callable, TypeVar, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_factor: float = 0.1,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add jitter to delays
            jitter_factor: Jitter factor (0-1)
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_factor = jitter_factor


class RetryHandler:
    """
    Handles retries with exponential backoff and jitter.

    Features:
    - Exponential backoff
    - Jitter to prevent thundering herd
    - Configurable retry conditions
    - Detailed logging
    - Circuit breaker support (optional)
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry handler.

        Args:
            config: Optional retry configuration
        """
        self.config = config or RetryConfig()

    def calculate_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """
        Calculate delay for a retry attempt.

        Args:
            attempt: Current attempt number (0-indexed)
            retry_after: Optional server-specified retry delay

        Returns:
            Delay in seconds
        """
        # If server specifies retry delay, use it
        if retry_after is not None:
            return retry_after

        # Calculate exponential backoff
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )

        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_factor
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable] = None,
        **kwargs
    ) -> T:
        """
        Execute a function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            retryable_exceptions: Tuple of exceptions that trigger retry
            on_retry: Optional callback called on each retry
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            The last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success!
                if attempt > 0:
                    logger.info(f"Succeeded after {attempt + 1} attempts")

                return result

            except retryable_exceptions as e:
                last_exception = e

                # Don't retry on last attempt
                if attempt == self.config.max_attempts - 1:
                    logger.error(
                        f"All {self.config.max_attempts} attempts failed: {e}"
                    )
                    raise

                # Extract retry_after from exception if available
                retry_after = None
                if hasattr(e, 'retry_after') and e.retry_after:
                    retry_after = float(e.retry_after)

                # Calculate delay
                delay = self.calculate_delay(attempt, retry_after)

                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )

                # Call retry callback if provided
                if on_retry:
                    try:
                        if asyncio.iscoroutinefunction(on_retry):
                            await on_retry(attempt, e, delay)
                        else:
                            on_retry(attempt, e, delay)
                    except Exception as callback_error:
                        logger.error(f"Retry callback failed: {callback_error}")

                # Wait before retry
                await asyncio.sleep(delay)

            except Exception as e:
                # Non-retryable exception
                logger.error(f"Non-retryable exception: {e}")
                raise

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for adding retry logic to async functions.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add jitter
        retryable_exceptions: Exceptions that trigger retry

    Example:
        @with_retry(max_attempts=3, retryable_exceptions=(RateLimitError,))
        async def call_api():
            # API call that might fail
            pass
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
    )

    handler = RetryHandler(config)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await handler.execute_with_retry(
                func,
                *args,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
        return wrapper

    return decorator


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    States:
    - CLOSED: Normal operation
    - OPEN: All requests fail immediately
    - HALF_OPEN: Test if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before testing recovery
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

        self.lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        async with self.lock:
            # Check if we should try to recover
            if self.state == "OPEN":
                if (
                    self.last_failure_time
                    and asyncio.get_event_loop().time() - self.last_failure_time
                    > self.recovery_timeout
                ):
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise CircuitBreakerError("Circuit breaker is OPEN")

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success! Reset if we were testing
            async with self.lock:
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("Circuit breaker recovered, now CLOSED")

            return result

        except self.expected_exception as e:
            async with self.lock:
                self.failure_count += 1
                self.last_failure_time = asyncio.get_event_loop().time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(
                        f"Circuit breaker opened after {self.failure_count} failures"
                    )

            raise

    def reset(self):
        """Manually reset the circuit breaker."""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Global retry handler instances
_default_handler = RetryHandler()
_aggressive_handler = RetryHandler(
    RetryConfig(
        max_attempts=5,
        initial_delay=0.5,
        max_delay=30.0,
    )
)


# Convenience functions
async def retry(
    func: Callable,
    *args,
    max_attempts: int = 3,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    **kwargs
) -> T:
    """Execute function with retry logic."""
    handler = RetryHandler(RetryConfig(max_attempts=max_attempts))
    return await handler.execute_with_retry(
        func,
        *args,
        retryable_exceptions=retryable_exceptions,
        **kwargs
    )
