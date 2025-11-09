# Internal Tools OpenAPI Specification

OpenAPI 3.1.0 specification for internal AI dev team tools.

## Overview

This specification defines 15 tools across 3 categories:

- **GitHub Operations** (6 tools): Issues, PRs, Projects, Actions
- **Code Operations** (5 tools): Analysis, Testing, Refactoring, Documentation, Migration
- **CI/CD Operations** (4 tools): Testing, Linting, Security Scanning, Preview Deployments

## Tools

### GitHub Operations

1. **createIssues** - Create multiple GitHub issues from specification
2. **createPR** - Create a pull request
3. **reviewPR** - Analyze and review a pull request
4. **updateIssue** - Update issue status and labels
5. **addToProject** - Add issue or PR to project board
6. **triggerWorkflow** - Trigger a GitHub Actions workflow

### Code Operations

1. **analyzeCode** - Run static code analysis
2. **generateTests** - Generate test cases for code
3. **refactorCode** - Apply code refactoring
4. **generateDocumentation** - Generate code documentation
5. **planMigration** - Create migration plan for code changes

### CI/CD Operations

1. **runTests** - Execute test suite
2. **runLinters** - Run code linters
3. **runSecurityScan** - Run security vulnerability scan
4. **deployPreview** - Create preview deployment

## Usage

### Loading into Tool Registry

```typescript
import { ToolRegistry } from '@ai-company/openapi-tools';

const registry = new ToolRegistry();
await registry.loadSpecs(['tools/openapi/ai-dev-tools.yaml']);

// Get all tools
const tools = registry.getToolSpecs();
console.log(`Loaded ${tools.length} tools`);

// Get GitHub tools
const githubTools = registry.getToolsByTag('github');
```

### Converting for LLM Providers

```typescript
import { convertToolSpec } from '@ai-company/openapi-tools';

const tool = registry.getToolByName('createPR');

// Convert for OpenAI
const openAITool = convertToolSpec(tool!, 'openai');

// Convert for Anthropic
const anthropicTool = convertToolSpec(tool!, 'anthropic');
```

## Validation

Validate the OpenAPI spec using:

```bash
# Using swagger-cli
npx swagger-cli validate tools/openapi/ai-dev-tools.yaml

# Using openapi-validator
npx @apidevtools/swagger-cli validate tools/openapi/ai-dev-tools.yaml
```

## Related Issues

- Issue #10: Internal Tools OpenAPI Specification ✅

## License

MIT

