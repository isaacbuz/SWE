# @ai-company/external-api-tools

Secure wrappers around external APIs (GitHub, GSA, etc.) with credential management and rate limiting.

## Overview

This package provides secure wrappers around external APIs that can be used as tools by LLMs. Credentials are managed separately and never exposed to LLMs.

## Features

- ✅ Secure credential management
- ✅ Rate limiting per API
- ✅ Retry logic with exponential backoff
- ✅ Response caching where appropriate
- ✅ Error handling and sanitization

## Installation

```bash
pnpm add @ai-company/external-api-tools
```

## Usage

### GitHub API Wrapper

```typescript
import { GitHubToolWrapper, EnvironmentCredentialVault } from '@ai-company/external-api-tools';

const vault = new EnvironmentCredentialVault();
const wrapper = new GitHubToolWrapper(vault, 'isaacbuz', 'SWE');

// Create issues
const result = await wrapper.createIssues({
  owner: 'isaacbuz',
  repo: 'SWE',
  tasks: [
    {
      title: 'Implement feature X',
      body: 'Description...',
      labels: ['enhancement'],
    },
  ],
});

console.log(`Created ${result.issues.length} issues`);
```

### Credential Management

```typescript
import { EnvironmentCredentialVault } from '@ai-company/external-api-tools';

const vault = new EnvironmentCredentialVault();

// Credentials are read from environment variables:
// GITHUB_TOKEN, GSA_API_KEY, etc.

const hasGitHub = await vault.hasCredentials('github');
if (hasGitHub) {
  const creds = await vault.getCredentials('github');
  // Use credentials securely (never expose to LLMs)
}
```

## Security

- **No credentials in code**: All credentials come from environment variables or secure vaults
- **No credentials in responses**: Tool results never include credentials
- **Input sanitization**: All user-provided data is sanitized
- **Rate limiting**: Prevents API abuse

## Rate Limiting

Rate limits are enforced per API:

- **GitHub**: 5000 req/hour (authenticated)
- **GSA APIs**: Varies by endpoint

## Related Packages

- `@ai-company/tool-executor` - Tool execution engine
- `@ai-company/openapi-tools` - OpenAPI tool registry

## License

MIT

