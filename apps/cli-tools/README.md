# CLI Tools

Command-line tools for AI-powered development workflows.

## Installation

```bash
pnpm install
pnpm build
```

## Commands

### spec-to-github

Convert a specification document to GitHub issues using AI.

```bash
pnpm run spec-to-github \
  --spec ./examples/auth-feature.md \
  --owner isaacbuz \
  --repo my-app \
  --provider openai
```

**Options:**
- `-s, --spec <path>` - Path to specification file (required)
- `-o, --owner <owner>` - GitHub repository owner (required)
- `-r, --repo <repo>` - GitHub repository name (required)
- `-p, --provider <provider>` - LLM provider (openai|anthropic), default: openai
- `-m, --model <model>` - Model name, default: gpt-4
- `-v, --verbose` - Verbose output
- `--dry-run` - Dry run (don't actually create issues)

**Environment Variables:**
- `OPENAI_API_KEY` - OpenAI API key (required if using openai provider)
- `ANTHROPIC_API_KEY` - Anthropic API key (required if using anthropic provider)
- `GITHUB_TOKEN` - GitHub personal access token (required for creating issues)

**Example:**

```bash
export OPENAI_API_KEY="sk-..."
export GITHUB_TOKEN="ghp_..."

pnpm run spec-to-github \
  --spec ./examples/auth-feature.md \
  --owner isaacbuz \
  --repo SWE \
  --provider openai \
  --verbose
```

**Output:**
```
🤖 Spec to GitHub Issues Pipeline

📄 Loading specification from: ./examples/auth-feature.md
✅ Loaded specification (1234 characters)
🔧 Initializing tool registry...
✅ Loaded 15 tools
⚙️  Setting up tool executor...
✅ Tool executor ready
🤖 Initializing openai provider...
✅ Provider ready: openai
🔗 Creating tool calling pipeline...
✅ Pipeline ready

📋 Analyzing specification and creating issues...

✅ Pipeline execution complete!

Results:
  Final Response: I've analyzed the specification and created 5 GitHub issues...
  Tool Executions: 1
  Total Turns: 1
  Execution Time: 2345ms

  ✓ Created issue #42: Implement user registration with email/password
    https://github.com/isaacbuz/SWE/issues/42
  ✓ Created issue #43: Add OAuth integration (Google and GitHub)
    https://github.com/isaacbuz/SWE/issues/43
  ✓ Created issue #44: Implement JWT token management
    https://github.com/isaacbuz/SWE/issues/44
  ✓ Created issue #45: Add security features (rate limiting, CSRF protection)
    https://github.com/isaacbuz/SWE/issues/45
  ✓ Created issue #46: Implement user profile management

✅ Successfully created 5 issues: #42, #43, #44, #45, #46
```

## Examples

Example specification files are available in the `examples/` directory:
- `auth-feature.md` - User authentication feature
- `api-integration.md` - External API integration

## Development

```bash
# Build
pnpm build

# Run in development mode
pnpm run spec-to-github --spec ./examples/auth-feature.md --owner test --repo test --dry-run
```

