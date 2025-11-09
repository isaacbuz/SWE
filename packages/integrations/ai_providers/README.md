# AI Provider Integrations

Complete integration layer for multiple AI providers with unified interface, advanced features, and production-ready utilities.

## Overview

This package provides a consistent interface for interacting with various AI providers:

- **Anthropic Claude** - Advanced reasoning, tool use, prompt caching
- **OpenAI GPT** - Industry standard, structured outputs, vision
- **Google Gemini** - Long context, multimodal capabilities
- **IBM Granite** - Code-specialized models, enterprise features
- **Local Models** - Privacy-first, zero-cost inference (Ollama/vLLM)

## Features

### Core Capabilities

- **Unified Interface**: Single API for all providers via `AIProvider` protocol
- **Streaming Support**: Real-time response streaming for all providers
- **Function Calling**: Tool use and structured outputs
- **Error Handling**: Automatic retries with exponential backoff
- **Rate Limiting**: Per-provider rate limiting with token awareness
- **Cost Tracking**: Automatic cost estimation and monitoring
- **Token Management**: Accurate token counting and compression

### Advanced Features

- **Prompt Caching** (Anthropic): Reduce costs for repeated context
- **Sub-Agents** (Anthropic): Claude can spawn sub-tasks
- **Vision Support**: Image analysis (OpenAI, Anthropic, Google)
- **JSON Mode**: Guaranteed JSON responses (OpenAI, Google)
- **Multimodal**: Text, images, video, audio (Google)
- **Local Inference**: Run models on-premises for sensitive data

## Installation

```bash
# Install base dependencies
pip install httpx pydantic

# Optional: For accurate token counting
pip install tiktoken

# Optional: For local models
# Install Ollama: https://ollama.ai
# Or vLLM: pip install vllm
```

## Quick Start

### Basic Usage

```python
import asyncio
from ai_providers.anthropic_client import AnthropicClient
from ai_providers.base import Message

async def main():
    # Initialize client
    async with AnthropicClient(api_key="your-key") as client:
        # Create messages
        messages = [
            Message(role="user", content="Explain quantum computing in simple terms")
        ]

        # Get completion
        completion = await client.complete(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=1000
        )

        print(completion.content)
        print(f"Tokens used: {completion.usage.total_tokens}")

asyncio.run(main())
```

### Streaming Responses

```python
async def stream_example():
    async with AnthropicClient() as client:
        messages = [
            Message(role="user", content="Write a short story")
        ]

        async for chunk in client.stream_complete(
            messages=messages,
            model="claude-3-5-sonnet-20241022"
        ):
            if chunk.content:
                print(chunk.content, end="", flush=True)
            if chunk.finish_reason:
                print(f"\n[Finished: {chunk.finish_reason}]")

asyncio.run(stream_example())
```

### Function Calling / Tool Use

```python
from ai_providers.base import Tool

async def tool_example():
    # Define tools
    tools = [
        Tool(
            name="get_weather",
            description="Get current weather for a location",
            parameters={
                "location": {
                    "type": "string",
                    "description": "City name"
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature units"
                }
            },
            required=["location"]
        )
    ]

    async with AnthropicClient() as client:
        messages = [
            Message(role="user", content="What's the weather in San Francisco?")
        ]

        completion = await client.complete(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            tools=tools
        )

        # Check if model wants to call a tool
        if completion.tool_calls:
            for tool_call in completion.tool_calls:
                print(f"Tool: {tool_call.name}")
                print(f"Arguments: {tool_call.arguments}")

asyncio.run(tool_example())
```

### Multi-Provider Usage

```python
from ai_providers.base import ProviderRegistry
from ai_providers.anthropic_client import AnthropicClient
from ai_providers.openai_client import OpenAIClient
from ai_providers.google_client import GoogleClient

async def multi_provider_example():
    # Create registry
    registry = ProviderRegistry()

    # Register providers
    registry.register("anthropic", AnthropicClient())
    registry.register("openai", OpenAIClient())
    registry.register("google", GoogleClient())

    # Get all available models
    models = await registry.get_available_models()

    for provider, model_list in models.items():
        print(f"\n{provider}:")
        for model in model_list:
            print(f"  - {model.name} (ctx: {model.context_window})")

    # Use specific provider
    client = registry.get("anthropic")
    messages = [Message(role="user", content="Hello!")]
    completion = await client.complete(messages, model="claude-3-5-sonnet-20241022")

asyncio.run(multi_provider_example())
```

## Provider-Specific Features

### Anthropic Claude

```python
# Prompt caching for cost reduction
completion = await client.complete(
    messages=messages,
    model="claude-3-5-sonnet-20241022",
    system_prompt="Large context that will be cached...",
    enable_caching=True
)

# Check cache usage
if completion.usage.cache_read_tokens:
    print(f"Cache hit! Saved {completion.usage.cache_read_tokens} tokens")
```

### OpenAI GPT

```python
from ai_providers.openai_client import OpenAIClient

# JSON mode for structured outputs
completion = await client.complete(
    messages=messages,
    model="gpt-4o",
    json_mode=True
)

# Response will be valid JSON
import json
data = json.loads(completion.content)
```

### Google Gemini

```python
from ai_providers.google_client import GoogleClient

# Very long context (2M tokens!)
async with GoogleClient() as client:
    completion = await client.complete(
        messages=messages,
        model="gemini-1.5-pro",  # 2M context window
        max_tokens=8192
    )
```

### IBM Granite

```python
from ai_providers.ibm_client import IBMClient

# Code-optimized models
async with IBMClient() as client:
    messages = [
        Message(role="user", content="Write a Python function to merge sorted arrays")
    ]

    completion = await client.complete(
        messages=messages,
        model="granite-20b-code-instruct"
    )
```

### Local Models

```python
from ai_providers.local_client import LocalClient

# Ollama backend
async with LocalClient(backend="ollama") as client:
    # Refresh model list
    models = await client.refresh_models()

    messages = [Message(role="user", content="Hello!")]
    completion = await client.complete(
        messages=messages,
        model="llama2"  # Or any installed Ollama model
    )

# vLLM backend (high performance)
async with LocalClient(backend="vllm", base_url="http://localhost:8000") as client:
    # Same interface, different backend
    pass
```

## Utilities

### Token Counting

```python
from utils.token_counter import count_tokens, estimate_cost

# Count tokens
text = "Your prompt here..."
tokens = count_tokens(text, provider="openai", model="gpt-4o")
print(f"Tokens: {tokens}")

# Estimate cost
cost = estimate_cost(
    prompt_tokens=1000,
    completion_tokens=500,
    provider="openai",
    model="gpt-4o"
)
print(f"Estimated cost: ${cost:.4f}")
```

### Prompt Compression

```python
from utils.prompt_compressor import compress, calculate_savings

# Compress prompt
original = "Your very long prompt with lots of redundant content..."
compressed = compress(original, aggressive=False)

# Calculate savings
savings = calculate_savings(original, compressed)
print(f"Saved {savings['tokens_saved']} tokens ({savings['compression_ratio']:.1%})")
```

### Rate Limiting

```python
from utils.rate_limiter import get_limiter

# Get rate limiter for provider
limiter = get_limiter("anthropic")

# Use as context manager
async with limiter:
    # Request is automatically rate-limited
    completion = await client.complete(messages, model="claude-3-5-sonnet-20241022")

# Check current usage
usage = limiter.get_current_usage()
print(f"Requests remaining: {usage['requests_per_minute']['remaining']}")
```

### Retry Handler

```python
from utils.retry_handler import with_retry
from ai_providers.base import RateLimitError

# Decorator for automatic retries
@with_retry(
    max_attempts=3,
    retryable_exceptions=(RateLimitError, TimeoutError)
)
async def call_api():
    return await client.complete(messages, model="claude-3-5-sonnet-20241022")

# Will automatically retry on failures
completion = await call_api()
```

## Configuration

Configuration is centralized in `config/providers.yaml`:

```yaml
providers:
  anthropic:
    enabled: true
    rate_limits:
      requests_per_minute: 50
      tokens_per_minute: 40000
    # ... more config

defaults:
  temperature: 0.7
  max_tokens: 4096
```

Load configuration:

```python
import yaml

with open("config/providers.yaml") as f:
    config = yaml.safe_load(f)

# Use config values
rate_limit = config["providers"]["anthropic"]["rate_limits"]["requests_per_minute"]
```

## Error Handling

```python
from ai_providers.base import (
    AIProviderError,
    RateLimitError,
    AuthenticationError,
    InvalidRequestError,
    ModelNotFoundError
)

try:
    completion = await client.complete(messages, model="claude-3-5-sonnet-20241022")

except RateLimitError as e:
    print(f"Rate limited! Retry after {e.retry_after}s")

except AuthenticationError:
    print("Invalid API key")

except ModelNotFoundError:
    print("Model not found")

except InvalidRequestError as e:
    print(f"Invalid request: {e}")

except AIProviderError as e:
    print(f"Provider error: {e}")
```

## Provider Capabilities Matrix

| Feature            | Anthropic  | OpenAI    | Google       | IBM        | Local      |
| ------------------ | ---------- | --------- | ------------ | ---------- | ---------- |
| Text Completion    | ✅         | ✅        | ✅           | ✅         | ✅         |
| Streaming          | ✅         | ✅        | ✅           | ✅         | ✅         |
| Function Calling   | ✅         | ✅        | ✅           | ❌         | Limited    |
| Vision             | ✅         | ✅        | ✅           | ❌         | ❌         |
| JSON Mode          | via prompt | ✅        | ✅           | via prompt | via prompt |
| Prompt Caching     | ✅         | ❌        | ❌           | ❌         | ❌         |
| Max Context        | 200K       | 128K      | 2M           | 8K         | Varies     |
| Cost per 1M tokens | $3-$15     | $0.15-$10 | $0.075-$1.25 | $2-$12     | Free       |

## Model Selection Guide

### For Code Generation

1. **IBM Granite** - Specialized for code
2. **Claude 3.5 Sonnet** - Excellent reasoning
3. **GPT-4o** - Strong general coding

### For Analysis & Reasoning

1. **Claude 3 Opus** - Best reasoning
2. **Claude 3.5 Sonnet** - Balanced
3. **GPT-4 Turbo** - Strong analysis

### For Long Context

1. **Gemini 1.5 Pro** - 2M tokens
2. **Claude 3.5 Sonnet** - 200K tokens
3. **GPT-4o** - 128K tokens

### For Cost Optimization

1. **Gemini 1.5 Flash** - $0.075/$0.30 per 1M
2. **Claude 3.5 Haiku** - $1/$5 per 1M
3. **GPT-4o Mini** - $0.15/$0.60 per 1M

### For Sensitive Data

1. **Local (Ollama/vLLM)** - Zero external calls
2. **IBM watsonx.ai** - Enterprise compliance

## Best Practices

### 1. Use Rate Limiting

```python
from utils.rate_limiter import get_limiter

limiter = get_limiter("anthropic")

async with limiter:
    completion = await client.complete(messages, model="claude-3-5-sonnet-20241022")
```

### 2. Enable Prompt Caching (Claude)

```python
# Cache large system prompts
completion = await client.complete(
    messages=messages,
    model="claude-3-5-sonnet-20241022",
    system_prompt="Large repeated context...",
    enable_caching=True
)
```

### 3. Compress Long Prompts

```python
from utils.prompt_compressor import compress_messages

# Compress before sending
messages = compress_messages(messages, max_tokens=100000)
completion = await client.complete(messages, model="claude-3-5-sonnet-20241022")
```

### 4. Handle Errors Gracefully

```python
from utils.retry_handler import with_retry

@with_retry(max_attempts=3)
async def robust_call():
    return await client.complete(messages, model="claude-3-5-sonnet-20241022")
```

### 5. Monitor Costs

```python
from utils.token_counter import estimate_cost

cost = estimate_cost(
    completion.usage.prompt_tokens,
    completion.usage.completion_tokens,
    "anthropic",
    "claude-3-5-sonnet-20241022"
)

if cost > 0.10:  # 10 cents
    logger.warning(f"High cost request: ${cost:.4f}")
```

## Architecture

```
packages/integrations/
├── ai_providers/
│   ├── base.py              # Core interfaces & types
│   ├── anthropic_client.py  # Claude integration
│   ├── openai_client.py     # GPT integration
│   ├── google_client.py     # Gemini integration
│   ├── ibm_client.py        # Granite integration
│   ├── local_client.py      # Ollama/vLLM
│   └── README.md
├── utils/
│   ├── token_counter.py     # Token counting & cost estimation
│   ├── prompt_compressor.py # Prompt compression
│   ├── rate_limiter.py      # Rate limiting
│   └── retry_handler.py     # Retry logic & circuit breaker
└── config/
    └── providers.yaml       # Provider configuration
```

## Testing

```python
# Health check
async def test_health():
    async with AnthropicClient() as client:
        is_healthy = await client.health_check()
        print(f"Anthropic healthy: {is_healthy}")

# List models
async def test_models():
    async with OpenAIClient() as client:
        models = client.list_models()
        for model in models:
            print(f"{model.name}: {model.context_window} tokens")

# Test all providers
async def test_all():
    providers = [
        ("Anthropic", AnthropicClient()),
        ("OpenAI", OpenAIClient()),
        ("Google", GoogleClient()),
    ]

    for name, client in providers:
        async with client:
            healthy = await client.health_check()
            print(f"{name}: {'✅' if healthy else '❌'}")
```

## License

MIT

## Support

For issues and questions, please open a GitHub issue or contact the integration team.
