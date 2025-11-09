/**
 * GitHub Webhook Event Handlers
 * 
 * Pre-built handlers for common GitHub webhook events.
 */
import { WebhookEvent, WebhookHandler } from './GitHubWebhookHandler';

/**
 * Issue event handlers
 */
export const issueHandlers = {
  /**
   * Handle issue opened
   */
  opened: (callback: (issue: any) => Promise<void>): WebhookHandler => {
    return async (event: WebhookEvent) => {
      if (event.name === 'issues' && event.payload.action === 'opened') {
        await callback(event.payload.issue);
      }
    };
  },

  /**
   * Handle issue closed
   */
  closed: (callback: (issue: any) => Promise<void>): WebhookHandler => {
    return async (event: WebhookEvent) => {
      if (event.name === 'issues' && event.payload.action === 'closed') {
        await callback(event.payload.issue);
      }
    };
  },

  /**
   * Handle issue labeled
   */
  labeled: (callback: (issue: any, label: any) => Promise<void>): WebhookHandler => {
    return async (event: WebhookEvent) => {
      if (event.name === 'issues' && event.payload.action === 'labeled') {
        await callback(event.payload.issue, event.payload.label);
      }
    };
  },
};

/**
 * Pull request event handlers
 */
export const pullRequestHandlers = {
  /**
   * Handle PR opened
   */
  opened: (callback: (pr: any) => Promise<void>): WebhookHandler => {
    return async (event: WebhookEvent) => {
      if (event.name === 'pull_request' && event.payload.action === 'opened') {
        await callback(event.payload.pull_request);
      }
    };
  },

  /**
   * Handle PR closed
   */
  closed: (callback: (pr: any) => Promise<void>): WebhookHandler => {
    return async (event: WebhookEvent) => {
      if (event.name === 'pull_request' && event.payload.action === 'closed') {
        await callback(event.payload.pull_request);
      }
    };
  },

  /**
   * Handle PR merged
   */
  merged: (callback: (pr: any) => Promise<void>): WebhookHandler => {
    return async (event: WebhookEvent) => {
      if (
        event.name === 'pull_request' &&
        event.payload.action === 'closed' &&
        event.payload.pull_request.merged
      ) {
        await callback(event.payload.pull_request);
      }
    };
  },

  /**
   * Handle PR review submitted
   */
  reviewSubmitted: (callback: (pr: any, review: any) => Promise<void>): WebhookHandler => {
    return async (event: WebhookEvent) => {
      if (event.name === 'pull_request_review' && event.payload.action === 'submitted') {
        await callback(event.payload.pull_request, event.payload.review);
      }
    };
  },
};

/**
 * Push event handlers
 */
export const pushHandlers = {
  /**
   * Handle push to branch
   */
  branchPush: (callback: (ref: string, commits: any[]) => Promise<void>): WebhookHandler => {
    return async (event: WebhookEvent) => {
      if (event.name === 'push') {
        await callback(event.payload.ref, event.payload.commits);
      }
    };
  },
};

/**
 * Workflow run handlers
 */
export const workflowRunHandlers = {
  /**
   * Handle workflow run completed
   */
  completed: (callback: (run: any) => Promise<void>): WebhookHandler => {
    return async (event: WebhookEvent) => {
      if (
        event.name === 'workflow_run' &&
        event.payload.action === 'completed'
      ) {
        await callback(event.payload.workflow_run);
      }
    };
  },
};

