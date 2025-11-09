"""
Token Counter Utility

Provides accurate token counting for different AI providers
to enable cost estimation and context window management.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable, Tuple

logger = logging.getLogger(__name__)


class UnsupportedTokenizerError(Exception):
    """Raised when requesting a provider/model combination without support."""


@dataclass
class TokenCounterResult:
    """Structured result for token counting with metadata."""

    tokens: int
    provider: str
    model: Optional[str]
    method: str
    approximated: bool
    char_length: int
    word_length: int

    def __int__(self) -> int:
        return self.tokens


DEFAULT_PROVIDER_APPROXIMATION = {
    "openai": 3.9,
    "anthropic": 3.7,
    "google": 4.2,
    "ibm": 4.0,
}

MODEL_METADATA: Dict[str, Dict[str, Dict[str, Any]]] = {
    "openai": {
        "gpt-4-turbo-2024-04-09": {"context": 128_000, "pricing": (0.01, 0.03)},
        "gpt-4o": {"context": 128_000, "pricing": (0.0025, 0.01)},
        "gpt-4o-mini": {"context": 128_000, "pricing": (0.00015, 0.0006)},
        "gpt-3.5-turbo": {"context": 16_385, "pricing": (0.0005, 0.0015)},
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {"context": 200_000, "pricing": (0.003, 0.015)},
        "claude-3-opus-20240229": {"context": 200_000, "pricing": (0.015, 0.075)},
        "claude-3-5-haiku-20241022": {"context": 200_000, "pricing": (0.001, 0.005)},
    },
    "google": {
        "gemini-1.5-pro": {"context": 2_000_000, "pricing": (0.00125, 0.005)},
        "gemini-1.5-flash": {"context": 1_000_000, "pricing": (0.000075, 0.0003)},
        "gemini-pro": {"context": 32_768, "pricing": (0.0005, 0.0015)},
    },
    "ibm": {
        "granite-20b-code-instruct": {"context": 8_192, "pricing": (0.002, 0.008)},
        "granite-34b-code-instruct": {"context": 8_192, "pricing": (0.003, 0.012)},
        "granite-3b-code-base": {"context": 8_192, "pricing": (0.0005, 0.002)},
    },
}



class TokenCounter:
    """
    Multi-provider token counter with graceful fallbacks.

    Supports accurate token counting for different providers while
    exposing structured metadata that can be used for cost estimation
    and context window management.
    """

    def __init__(self):
        self._encoders: Dict[str, Any] = {}
        self._custom_counters: Dict[str, Callable[[str, Optional[str]], Tuple[int, str, bool]]] = {}
        self._load_encoders()

    # ------------------------------------------------------------------
    # Registration & configuration
    # ------------------------------------------------------------------
    def register_model(
        self,
        provider: str,
        model: str,
        *,
        context: Optional[int] = None,
        pricing: Optional[Tuple[float, float]] = None
    ) -> None:
        """Register or override metadata for a model."""
        provider = provider.lower()
        MODEL_METADATA.setdefault(provider, {})
        MODEL_METADATA[provider][model] = MODEL_METADATA[provider].get(model, {})
        if context is not None:
            MODEL_METADATA[provider][model]["context"] = context
        if pricing is not None:
            MODEL_METADATA[provider][model]["pricing"] = pricing

    def register_encoder(self, provider: str, encoder: Any) -> None:
        """Register a custom encoder/tokenizer module."""
        self._encoders[provider.lower()] = encoder

    def register_counter(
        self,
        provider: str,
        counter: Callable[[str, Optional[str]], Tuple[int, str, bool]]
    ) -> None:
        """Register a callable that returns (tokens, method, approximated) for a provider."""
        self._custom_counters[provider.lower()] = counter

    def _load_encoders(self) -> None:
        """Attempt to load known tokenizer encoders."""
        try:
            import tiktoken

            self._encoders["openai"] = tiktoken
            logger.info("Loaded tiktoken for OpenAI token counting")
        except ImportError:
            logger.info("tiktoken not installed; OpenAI counting will use approximation")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def count_tokens(
        self,
        text: str,
        provider: str = "openai",
        model: Optional[str] = None,
        *,
        detailed: bool = False
    ) -> int | TokenCounterResult:
        """Count tokens and optionally return structured metadata."""
        result = self._count_tokens_with_details(text, provider, model)
        return result if detailed else result.tokens

    def count_tokens_with_details(
        self,
        text: str,
        provider: str = "openai",
        model: Optional[str] = None,
    ) -> TokenCounterResult:
        """Convenience wrapper for callers that always need metadata."""
        return self._count_tokens_with_details(text, provider, model)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _count_tokens_with_details(
        self,
        text: str,
        provider: str,
        model: Optional[str]
    ) -> TokenCounterResult:
        provider = (provider or "openai").lower()
        char_len = len(text)
        word_len = len(text.split())

        counter = self._custom_counters.get(provider)
        if counter:
            tokens, method, approximated = counter(text, model)
            return self._result(tokens, provider, model, method, approximated, char_len, word_len)

        strategy = None
        tokens = None
        approximated = False

        if provider == "openai" and "openai" in self._encoders:
            tokens, strategy, approximated = self._count_openai_tokens(text, model)
        elif provider == "anthropic":
            tokens, strategy, approximated = self._count_anthropic_tokens(text, model)
        elif provider == "google":
            tokens, strategy, approximated = self._count_google_tokens(text, model)

        if tokens is None:
            tokens = self._approximate_tokens(text, provider)
            strategy = "approximation"
            approximated = True

        return self._result(tokens, provider, model, strategy, approximated, char_len, word_len)

    def _result(
        self,
        tokens: int,
        provider: str,
        model: Optional[str],
        method: str,
        approximated: bool,
        char_length: int,
        word_length: int,
    ) -> TokenCounterResult:
        return TokenCounterResult(
            tokens=tokens,
            provider=provider,
            model=model,
            method=method,
            approximated=approximated,
            char_length=char_length,
            word_length=word_length,
        )

    def _count_openai_tokens(self, text: str, model: Optional[str]) -> Tuple[Optional[int], str, bool]:
        """Count tokens using OpenAI's tiktoken encoder when available."""
        try:
            tiktoken = self._encoders.get("openai")
            if tiktoken:
                encoding = tiktoken.encoding_for_model(model or "gpt-4o")
                return len(encoding.encode(text)), "tiktoken-openai", False
        except Exception as exc:
            logger.warning("Error using tiktoken (%s); falling back to approximation", exc)
        return None, "approximation", True

    def _count_anthropic_tokens(self, text: str, model: Optional[str]) -> Tuple[Optional[int], str, bool]:
        """
        Count tokens for Anthropic Claude.

        Uses tiktoken as a close proxy when available, since the tokenization
        scheme is comparable. Marks the result as approximated to signal that
        it is not exact.
        """
        if "openai" in self._encoders:
            tokens, _, _ = self._count_openai_tokens(text, model or "gpt-4o")
            if tokens is not None:
                return tokens, "tiktoken-openai-proxy", True
        return None, "approximation", True

    def _count_google_tokens(self, text: str, model: Optional[str]) -> Tuple[Optional[int], str, bool]:
        """
        Count tokens for Google Gemini.

        Google uses SentencePiece. Until an official encoder is published, we
        use a calibrated approximation multiplier.
        """
        approx = self._approximate_tokens(text, "google")
        return int(approx * 1.05), "approximation-google", True

    def _approximate_tokens(self, text: str, provider: Optional[str] = None) -> int:
        """Approximate token count based on provider heuristics."""
        words = len(text.split())
        chars = len(text)
        ratio = DEFAULT_PROVIDER_APPROXIMATION.get(provider or "openai", 4.0)

        char_based = max(1, int(chars / ratio))
        word_based = max(1, int(words * 1.3))

        return max(char_based, word_based)

    def _get_model_metadata(self, provider: str, model: Optional[str]) -> Dict[str, Any]:
        """Lookup metadata for a provider/model pair."""
        provider = (provider or "openai").lower()
        if not model:
            return {}
        return MODEL_METADATA.get(provider, {}).get(model, {})

    def count_messages_tokens(
        self,
        messages: List[Dict[str, Any]],
        provider: str = "openai",
        model: Optional[str] = None
    ) -> int:
        """
        Count tokens for a list of chat messages, including provider-specific overhead.
        """
        provider = (provider or "openai").lower()
        total = 0

        if provider == "openai":
            total += len(messages) * 4  # per-message overhead
            total += 2  # priming tokens
        elif provider == "anthropic":
            total += len(messages) * 3

        for message in messages:
            content = message.get("content", "")
            if isinstance(content, str):
                total += self.count_tokens(content, provider, model)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text")
                        if text:
                            total += self.count_tokens(text, provider, model)

            role = message.get("role", "")
            if role:
                total += self.count_tokens(role, provider, model)

        return total

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        provider: str,
        model: str
    ) -> float:
        """Estimate cost for an API call using metadata when available."""
        metadata = self._get_model_metadata(provider, model)
        pricing = metadata.get("pricing")
        if not pricing:
            logger.warning("No pricing info for %s/%s", provider, model)
            return 0.0

        prompt_cost, completion_cost = pricing
        return (
            (prompt_tokens / 1000) * prompt_cost
            + (completion_tokens / 1000) * completion_cost
        )

    def fits_context_window(
        self,
        token_count: int,
        provider: str,
        model: str,
        reserve_for_completion: int = 1000
    ) -> bool:
        """Check if the provided tokens fit within the model's context window."""
        metadata = self._get_model_metadata(provider, model)
        context_limit = metadata.get("context")
        if context_limit is None:
            logger.warning("No context window info for %s/%s", provider, model)
            return True
        return token_count + reserve_for_completion <= context_limit


# Global instance
_counter = TokenCounter()


# Convenience functions
def count_tokens(text: str, provider: str = "openai", model: Optional[str] = None) -> int:
    """Count tokens in text."""
    return _counter.count_tokens(text, provider, model)


def count_tokens_with_details(
    text: str,
    provider: str = "openai",
    model: Optional[str] = None,
) -> TokenCounterResult:
    """Count tokens and return detailed metadata."""
    return _counter.count_tokens_with_details(text, provider, model)


def count_messages_tokens(
    messages: List[Dict[str, Any]],
    provider: str = "openai",
    model: Optional[str] = None
) -> int:
    """Count tokens for messages."""
    return _counter.count_messages_tokens(messages, provider, model)


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    provider: str,
    model: str
) -> float:
    """Estimate API call cost."""
    return _counter.estimate_cost(prompt_tokens, completion_tokens, provider, model)


def fits_context_window(
    token_count: int,
    provider: str,
    model: str,
    reserve_for_completion: int = 1000
) -> bool:
    """Check if tokens fit in context window."""
    return _counter.fits_context_window(token_count, provider, model, reserve_for_completion)
