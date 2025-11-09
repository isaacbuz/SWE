# Architecture Overview

## System Components

The OpenAPI Tools system consists of several key components:

### 1. Tool Registry
**Package**: `@ai-company/openapi-tools`  
**Purpose**: Manages tool definitions loaded from OpenAPI specifications

**Key Features**:
- Loads OpenAPI 3.0/3.1 specifications
- Converts operations to tool specifications
- Provides tool discovery and lookup
- Supports multiple spec merging

### 2. Tool Executor
**Package**: `@ai-company/openapi-tools`  
**Purpose**: Executes tools with validation, rate limiting, and security

**Key Features**:
- Schema validation using Zod
- Rate limiting (per-user, per-tool, global)
- Circuit breaker for fault tolerance
- Permission checking
- Input sanitization

### 3. Permission System
**Package**: `@ai-company/openapi-tools`  
**Purpose**: Role-based access control for tool execution

**Key Features**:
- Role definitions (admin, developer, agent, readonly)
- Permission inheritance
- Fine-grained conditions
- Custom permissions per user

### 4. Tool Calling Pipeline
**Package**: `@ai-company/tool-pipeline`  
**Purpose**: Orchestrates multi-turn LLM-tool interactions

**Key Features**:
- Multi-turn conversation loops
- Tool discovery and conversion
- Parallel tool execution
- Result integration

### 5. External API Wrappers
**Package**: `@ai-company/external-api-tools`  
**Purpose**: Secure wrappers for external APIs

**Key Features**:
- GitHub API integration
- GSA API integration
- Credential management
- Response caching
- Retry logic

## Data Flow

```
User Request
    ↓
Tool Calling Pipeline
    ↓
LLM Provider (with tool specs)
    ↓
Tool Calls Detected
    ↓
Tool Executor
    ├── Permission Check
    ├── Schema Validation
    ├── Rate Limit Check
    ├── Circuit Breaker Check
    └── Execute Tool
    ↓
External API / Tool Handler
    ↓
Tool Results
    ↓
LLM Provider (with results)
    ↓
Final Response to User
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Request                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Tool Calling Pipeline                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Tool Registry│  │ Tool Executor│  │ LLM Provider │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Security & Validation Layer                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Permissions  │  │ Rate Limiter │  │ Validator    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            External API Wrappers                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ GitHub API   │  │ GSA API      │  │ Custom APIs  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Component Interactions

### Tool Registry → Tool Executor
- Registry provides tool specifications
- Executor uses specs for validation

### Tool Executor → Permission Checker
- Executor checks permissions before execution
- Permission checker validates user roles and permissions

### Tool Executor → Rate Limiter
- Executor checks rate limits before execution
- Rate limiter tracks usage and enforces limits

### Tool Calling Pipeline → LLM Provider
- Pipeline converts tool specs to provider format
- Provider generates tool calls based on user request

### Tool Calling Pipeline → Tool Executor
- Pipeline executes tool calls via executor
- Executor returns results to pipeline
- Pipeline integrates results into conversation

## Security Model

1. **Authentication**: User identity verified
2. **Authorization**: Permission checker validates access
3. **Validation**: Schema validator ensures correct inputs
4. **Rate Limiting**: Prevents abuse
5. **Audit Logging**: All executions logged
6. **Input Sanitization**: Prevents injection attacks

## Scalability

- **Horizontal Scaling**: Stateless components
- **Caching**: Response caching reduces API calls
- **Rate Limiting**: Prevents overload
- **Circuit Breaker**: Prevents cascading failures

## Error Handling

- **Validation Errors**: Caught and returned with details
- **Permission Errors**: Clear error messages
- **Rate Limit Errors**: Retry-after information
- **Tool Execution Errors**: Logged and returned
- **LLM Errors**: Handled gracefully with fallbacks

