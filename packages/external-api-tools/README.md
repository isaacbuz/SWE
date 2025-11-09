# External API Tools

Wrappers for external APIs (GitHub, GSA, etc.) with credential management, rate limiting, caching, and retries.

## Features

- ✅ GitHub API wrapper (issues, PRs, repositories)
- ✅ GSA/Data.gov API wrapper (SAM entities, contract opportunities)
- ✅ Secure credential management (never exposed to LLMs)
- ✅ Response caching to reduce API calls
- ✅ Automatic retry with exponential backoff
- ✅ Rate limiting compliance
- ✅ TypeScript types for all operations

## Installation

```bash
pnpm add @ai-company/external-api-tools
```

## Usage

### GitHub API Wrapper

```typescript
import {
  GitHubToolWrapper,
  CredentialVault,
} from "@ai-company/external-api-tools";

const vault = new CredentialVault();
const github = new GitHubToolWrapper(vault);

// Set credentials (from environment or secure storage)
github.setCredentials({
  apiKey: process.env.GITHUB_TOKEN,
});

// Create issues
const result = await github.createIssues({
  owner: "isaacbuz",
  repo: "SWE",
  tasks: [
    {
      title: "Implement feature X",
      body: "Description...",
      labels: ["enhancement"],
    },
  ],
});

// Create PR
const pr = await github.createPR({
  owner: "isaacbuz",
  repo: "SWE",
  title: "feat: Add feature X",
  head: "feature/x",
  base: "main",
});
```

### GSA API Wrapper

```typescript
import {
  GSAToolWrapper,
  CredentialVault,
} from "@ai-company/external-api-tools";

const vault = new CredentialVault();
const gsa = new GSAToolWrapper(vault);

// Set credentials
gsa.setCredentials({
  apiKey: process.env.GSA_API_KEY,
});

// Search SAM entities
const entities = await gsa.searchSAMEntity({
  query: "technology company",
  limit: 10,
});

// Search contract opportunities
const opportunities = await gsa.searchContractOpportunities({
  query: "software development",
  posted_from: "2024-01-01",
});
```

## Security

- Credentials are stored securely and never exposed in logs or responses
- All API calls use HTTPS
- Credentials are validated before use
- No credentials are included in error messages

## License

MIT
