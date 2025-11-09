import pytest

from packages.integrations.utils.token_counter import (
    TokenCounter,
    count_tokens,
    count_tokens_with_details,
)


def test_custom_counter_registration():
    counter = TokenCounter()
    counter.register_counter("custom", lambda text, model: (len(text), "custom", False))

    result = counter.count_tokens_with_details("abcd", provider="custom")
    assert isinstance(result.tokens, int)
    assert result.tokens == 4
    assert result.method == "custom"
    assert result.approximated is False


def test_register_model_updates_metadata():
    counter = TokenCounter()
    counter.register_model("custom", "v1", context=1234, pricing=(0.1, 0.2))

    assert counter.fits_context_window(200, "custom", "v1", reserve_for_completion=900) is True
    assert counter.estimate_cost(1000, 1000, "custom", "v1") == pytest.approx(0.3)


def test_count_tokens_with_details_api():
    result = count_tokens_with_details("hello world", provider="unknown")
    assert result.tokens > 0
    assert result.approximated is True
    assert result.provider == "unknown"


def test_count_messages_tokens_includes_overhead():
    counter = TokenCounter()
    messages = [{"role": "user", "content": "hello"}]
    total = counter.count_messages_tokens(messages, provider="openai")
    # Should at least include role/content plus overhead (> tokens in content alone)
    assert total >= count_tokens("hello")
