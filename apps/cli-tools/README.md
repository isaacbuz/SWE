# CLI Tools

Command-line tools for AI Dev Team operations, including the spec-to-github pipeline.

## Installation

```bash
pnpm install
pnpm build
```

## Commands

### spec-to-github

Convert a specification document into GitHub issues using LLM + tools.

**Usage:**
```bash
pnpm run spec-to-github \
  --spec ./examples/feature-spec.md \
  --owner isaacbuz \
  --repo my-app \
  --provider openai \
  --verbose
```

**Options:**
- `-s, --spec <path>` - Path to specification file (required)
- `-o, --owner <owner>` - GitHub repository owner (required)
- `-r, --repo <repo>` - GitHub repository name (required)
- `-p, --provider <provider>` - LLM provider (openai, anthropic) (default: openai)
- `-v, --verbose` - Enable verbose logging

**Example:**
```bash
pnpm run spec-to-github \
  --spec ./examples/user-auth-spec.md \
  --owner myorg \
  --repo myproject
```

## How It Works

1. **Loads specification** from the provided file
2. **Initializes tool registry** with OpenAPI tools
3. **Registers tool handlers** for GitHub operations
4. **Creates LLM provider** (OpenAI, Anthropic, etc.)
5. **Executes pipeline** with tool calling
6. **Creates GitHub issues** via the `createIssues` tool
7. **Displays results** with issue numbers and URLs

## Example Specification Format

```markdown
# Feature: User Authentication

## Overview
Implement JWT-based authentication system.

## Tasks

### Backend
- Create user model
- Implement JWT token generation
- Add password hashing

### Frontend
- Create login form
- Add token storage
- Implement protected routes
```

The pipeline will automatically break this down into structured GitHub issues.

## Integration

This CLI tool uses:
- `@ai-company/openapi-tools` - Tool registry and executor
- `@ai-company/tool-pipeline` - Tool calling pipeline
- GitHub API - For creating issues

## Development

```bash
# Build
pnpm build

# Run in development mode
pnpm dev

# Run specific command
pnpm run spec-to-github --spec ./examples/test.md --owner test --repo test
```

## License

MIT

