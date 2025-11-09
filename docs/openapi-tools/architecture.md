# OpenAPI Tools Architecture

## System Overview

The OpenAPI Tools system provides a unified interface for LLMs to discover, call, and execute tools defined in OpenAPI specifications.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Provider                         │
│              (OpenAI, Anthropic, etc.)                  │
└────────────────────┬──────────────────────────────────┘
                     │ Tool Calls
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Tool Calling Pipeline                      │
│  - Multi-turn orchestration                            │
│  - Tool result formatting                               │
│  - Cost tracking                                        │
└────────────────────┬──────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  Tool Registry  │    │ Tool Executor    │
│  - Load specs   │    │ - Validation     │
│  - Query tools  │    │ - Execution      │
│  - Convert      │    │ - Rate limiting │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌─────────────────────┐
         │   External APIs      │
         │  (GitHub, GSA, etc.) │
         └─────────────────────┘
```

## Components

### Tool Registry

**Purpose**: Load and manage OpenAPI tool specifications

**Key Features**:
- Load multiple OpenAPI 3.0/3.1 specs
- Extract tool definitions from operations
- Convert to provider-agnostic format
- Query by name, tag, or endpoint

**Location**: `packages/openapi-tools/`

### Tool Executor

**Purpose**: Securely execute tools with validation

**Key Features**:
- JSON Schema validation
- Rate limiting per tool
- Circuit breaker for failures
- Timeout and retry logic
- Audit logging integration

**Location**: `packages/tool-executor/`

### Tool Calling Pipeline

**Purpose**: Orchestrate multi-turn tool calling

**Key Features**:
- Multi-turn conversations
- Parallel tool execution
- Cost tracking
- Loop detection
- Error handling

**Location**: `packages/tool-pipeline/`

## Data Flow

1. **Tool Discovery**: Registry loads OpenAPI specs and extracts tools
2. **Tool Registration**: Executor registers tool handlers
3. **LLM Request**: User provides prompt with available tools
4. **Tool Calling**: LLM generates tool calls based on prompt
5. **Tool Execution**: Executor validates and executes tools
6. **Result Feeding**: Tool results fed back to LLM
7. **Completion**: LLM provides final answer

## Security

- **Input Validation**: All inputs validated against JSON Schema
- **Credential Management**: Credentials never exposed to LLMs
- **Rate Limiting**: Per-tool and per-user limits
- **Audit Logging**: Complete audit trail with PII redaction
- **Permissions**: RBAC for tool execution

## Performance

- **Caching**: Tool specs cached in registry
- **Parallel Execution**: Tools executed in parallel when safe
- **Cost Tracking**: Real-time cost estimation
- **Metrics**: Performance tracking per provider/tool

