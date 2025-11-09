# @ai-company/cli-tools

Command-line tools for AI development workflows.

## Tools

### spec-to-github

Convert specification documents into GitHub issues using AI.

## Installation

```bash
npm install @ai-company/cli-tools
```

## Usage

### Basic Usage

```bash
spec-to-github \
  --spec ./examples/auth-feature.md \
  --owner isaacbuz \
  --repo my-app
```

### Dry Run

Preview what issues would be created without actually creating them:

```bash
spec-to-github \
  --spec ./examples/auth-feature.md \
  --owner isaacbuz \
  --repo my-app \
  --dry-run
```

### Specify Provider

Use a specific LLM provider:

```bash
spec-to-github \
  --spec ./examples/auth-feature.md \
  --owner isaacbuz \
  --repo my-app \
  --provider openai
```

## Options

- `--spec <path>`: Path to specification file (required)
- `--owner <owner>`: GitHub repository owner (required)
- `--repo <repo>`: GitHub repository name (required)
- `--provider <provider>`: LLM provider (default: auto-select)
- `--dry-run`: Preview issues without creating them

## Example Output

```
🤖 Spec to GitHub Issues Pipeline
================================

📄 Loading specification from: ./examples/auth-feature.md
✓ Loaded 1,234 characters

🔧 Initializing AI pipeline with provider: auto
✓ Pipeline initialized

📋 Analyzing specification and planning issues...
✓ Analysis complete

📝 Creating GitHub issues...
✅ Created 3 issues: #42, #43, #44

📊 Pipeline Metrics:
   Duration: 3.2s
   Tokens: 1,234 in / 567 out
   Cost: $0.023
   Provider: openai:gpt-4

✨ Done!
```

## Examples

See the `examples/` directory for sample specification files.

## License

MIT
