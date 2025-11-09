import { Octokit } from '@octokit/rest';
import { CredentialVault, Credentials } from '../types/CredentialVault';
import { RateLimiter } from '../utils/RateLimiter';

/**
 * GitHub API Tool Wrapper
 * 
 * Provides secure wrappers around GitHub API operations.
 * Credentials are managed separately and never exposed to LLMs.
 */
export class GitHubToolWrapper {
  private octokit: Octokit | null = null;
  private rateLimiter: RateLimiter;

  constructor(
    private credentialVault: CredentialVault,
    private owner: string,
    private repo: string
  ) {
    // GitHub rate limits: 5000 req/hour for authenticated, 60 for unauthenticated
    this.rateLimiter = new RateLimiter({
      maxRequests: 5000,
      windowMs: 60 * 60 * 1000, // 1 hour
    });
  }

  /**
   * Initialize GitHub client with credentials
   */
  private async initialize(): Promise<void> {
    if (this.octokit) {
      return;
    }

    const credentials = await this.credentialVault.getCredentials('github');
    if (!credentials || !credentials.token) {
      throw new Error('GitHub credentials not found');
    }

    this.octokit = new Octokit({
      auth: credentials.token,
    });
  }

  /**
   * Create multiple GitHub issues
   */
  async createIssues(args: {
    owner: string;
    repo: string;
    tasks: Array<{
      title: string;
      body: string;
      labels?: string[];
      assignees?: string[];
      milestone?: string;
    }>;
  }): Promise<{ issues: Array<{ number: number; url: string; title: string }> }> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const issues = [];

    for (const task of args.tasks) {
      try {
        const response = await this.octokit.rest.issues.create({
          owner: args.owner,
          repo: args.repo,
          title: task.title,
          body: task.body,
          labels: task.labels,
          assignees: task.assignees,
          milestone: task.milestone ? parseInt(task.milestone, 10) : undefined,
        });

        issues.push({
          number: response.data.number,
          url: response.data.html_url,
          title: response.data.title,
        });
      } catch (error) {
        console.error(`Failed to create issue "${task.title}":`, error);
        throw error;
      }
    }

    return { issues };
  }

  /**
   * Create a pull request
   */
  async createPR(args: {
    owner: string;
    repo: string;
    title: string;
    body: string;
    head: string;
    base: string;
    draft?: boolean;
    labels?: string[];
    reviewers?: string[];
  }): Promise<{ number: number; url: string; title: string }> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.pulls.create({
      owner: args.owner,
      repo: args.repo,
      title: args.title,
      body: args.body,
      head: args.head,
      base: args.base,
      draft: args.draft ?? false,
    });

    // Add labels if provided
    if (args.labels && args.labels.length > 0) {
      await this.octokit.rest.issues.addLabels({
        owner: args.owner,
        repo: args.repo,
        issue_number: response.data.number,
        labels: args.labels,
      });
    }

    // Request reviews if provided
    if (args.reviewers && args.reviewers.length > 0) {
      await this.octokit.rest.pulls.requestReviewers({
        owner: args.owner,
        repo: args.repo,
        pull_number: response.data.number,
        reviewers: args.reviewers,
      });
    }

    return {
      number: response.data.number,
      url: response.data.html_url,
      title: response.data.title,
    };
  }

  /**
   * Update an issue
   */
  async updateIssue(args: {
    owner: string;
    repo: string;
    issueNumber: number;
    state?: 'open' | 'closed';
    labels?: string[];
    assignees?: string[];
    milestone?: string;
  }): Promise<void> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    await this.octokit.rest.issues.update({
      owner: args.owner,
      repo: args.repo,
      issue_number: args.issueNumber,
      state: args.state,
      labels: args.labels,
      assignees: args.assignees,
      milestone: args.milestone ? parseInt(args.milestone, 10) : undefined,
    });
  }

  /**
   * Merge a pull request
   */
  async mergePR(args: {
    owner: string;
    repo: string;
    prNumber: number;
    mergeMethod?: 'merge' | 'squash' | 'rebase';
    commitMessage?: string;
  }): Promise<void> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    await this.octokit.rest.pulls.merge({
      owner: args.owner,
      repo: args.repo,
      pull_number: args.prNumber,
      merge_method: args.mergeMethod ?? 'merge',
      commit_message: args.commitMessage,
    });
  }

  /**
   * Add comment to issue or PR
   */
  async commentOnIssue(args: {
    owner: string;
    repo: string;
    issueNumber: number;
    body: string;
  }): Promise<void> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    await this.octokit.rest.issues.createComment({
      owner: args.owner,
      repo: args.repo,
      issue_number: args.issueNumber,
      body: args.body,
    });
  }
}

