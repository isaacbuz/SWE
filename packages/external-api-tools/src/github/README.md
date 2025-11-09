# GitHub Integration

Complete GitHub API integration including Issues, Pull Requests, Projects, Actions, and Webhooks.

## GitHub Tool Wrapper

The `GitHubToolWrapper` provides secure wrappers around GitHub API operations.

### Usage

```typescript
import { GitHubToolWrapper, EnvironmentCredentialVault } from '@ai-company/external-api-tools';

const vault = new EnvironmentCredentialVault();
const github = new GitHubToolWrapper(vault, 'owner', 'repo');

// Create issue
const issue = await github.createIssue('owner', 'repo', 'Title', 'Body');

// List PRs
const prs = await github.listPRs('owner', 'repo', { state: 'open' });

// List workflows
const workflows = await github.listWorkflows('owner', 'repo');
```

## GitHub Webhook Handler

The `GitHubWebhookHandler` validates webhook signatures and routes events to handlers.

### Usage

```typescript
import {
  GitHubWebhookHandler,
  issueHandlers,
  pullRequestHandlers,
} from '@ai-company/external-api-tools';

const handler = new GitHubWebhookHandler(process.env.GITHUB_WEBHOOK_SECRET!);

// Handle issue opened
handler.on('issues', issueHandlers.opened(async (issue) => {
  console.log(`Issue #${issue.number} opened: ${issue.title}`);
}));

// Handle PR merged
handler.on('pull_request', pullRequestHandlers.merged(async (pr) => {
  console.log(`PR #${pr.number} merged: ${pr.title}`);
}));

// Express.js middleware
app.post('/webhooks/github', handler.middleware());
```

### Supported Events

- **Issues**: opened, closed, labeled, assigned
- **Pull Requests**: opened, closed, merged, review submitted
- **Push**: branch push events
- **Workflow Run**: completed events

### Security

All webhooks are verified using HMAC SHA-256 signatures. Invalid signatures are rejected.

## API Reference

See individual files for detailed API documentation:
- `GitHubToolWrapper.ts` - GitHub API operations
- `GitHubWebhookHandler.ts` - Webhook handling
- `webhookHandlers.ts` - Pre-built event handlers

