# CLI Tools

Command-line tools for AI agent workflows.

## Installation

```bash
pnpm install
pnpm build
```

## Commands

### spec-to-github

Convert a specification file into GitHub issues using AI.

```bash
# Using OpenAI
spec-to-github \
  --spec ./examples/auth-feature.md \
  --owner isaacbuz \
  --repo SWE \
  --openai-key $OPENAI_API_KEY \
  --token $GITHUB_TOKEN

# Using Anthropic
spec-to-github \
  --spec ./examples/auth-feature.md \
  --owner isaacbuz \
  --repo SWE \
  --anthropic-key $ANTHROPIC_API_KEY \
  --provider anthropic \
  --model claude-3-sonnet-20240229 \
  --token $GITHUB_TOKEN
```

## Examples

Example specification files are in `examples/`:

- `auth-feature.md` - User authentication feature
- `api-integration.md` - External API integration
- `ui-redesign.md` - UI component redesign

## License

MIT

