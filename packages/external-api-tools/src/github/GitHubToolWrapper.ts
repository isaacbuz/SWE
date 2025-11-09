/**
 * GitHub API Tool Wrapper
 *
 * Wraps GitHub API operations as OpenAPI-compatible tools.
 * Handles authentication, rate limiting, caching, and retries.
 */

import { CredentialVault, CredentialConfig } from "../utils/CredentialVault.js";
import { ResponseCache } from "../utils/ResponseCache.js";
import { RetryHandler } from "../utils/RetryHandler.js";

export interface CreateIssuesArgs {
  owner: string;
  repo: string;
  tasks: Array<{
    title: string;
    body: string;
    labels?: string[];
    assignees?: string[];
    milestone?: number;
    related_issues?: number[];
  }>;
}

export interface CreateIssuesResult {
  success: boolean;
  created: number;
  issues: Array<{
    number: number;
    url: string;
    title: string;
  }>;
}

export interface CreatePRArgs {
  owner: string;
  repo: string;
  title: string;
  head: string;
  base: string;
  body?: string;
  draft?: boolean;
  auto_merge?: boolean;
  reviewers?: string[];
  labels?: string[];
}

export interface CreatePRResult {
  success: boolean;
  pr_number: number;
  url: string;
}

export interface ReviewPRArgs {
  owner: string;
  repo: string;
  pr_number: number;
  review_type?: "security" | "performance" | "best_practices" | "comprehensive";
  include_suggestions?: boolean;
}

export interface ReviewPRResult {
  success: boolean;
  review: {
    summary: string;
    issues: Array<{
      severity: "critical" | "high" | "medium" | "low";
      file: string;
      line: number;
      message: string;
      suggestion?: string;
    }>;
    score: number;
  };
}

export class GitHubToolWrapper {
  private baseUrl = "https://api.github.com";
  private credentialVault: CredentialVault;
  private cache: ResponseCache;
  private retryHandler: RetryHandler;

  constructor(
    credentialVault: CredentialVault,
    cache?: ResponseCache,
    retryHandler?: RetryHandler,
  ) {
    this.credentialVault = credentialVault;
    this.cache = cache || new ResponseCache(300000); // 5 min default
    this.retryHandler = retryHandler || new RetryHandler();
  }

  /**
   * Set GitHub credentials
   */
  setCredentials(config: CredentialConfig): void {
    this.credentialVault.setCredentials("github", config);
  }

  /**
   * Create multiple GitHub issues
   */
  async createIssues(args: CreateIssuesArgs): Promise<CreateIssuesResult> {
    const authHeaders = this.credentialVault.getAuthHeader("github");
    if (!authHeaders) {
      throw new Error("GitHub credentials not configured");
    }

    const createdIssues = [];

    for (const task of args.tasks) {
      const issueData = await this.retryHandler.execute(async () => {
        const response = await fetch(
          `${this.baseUrl}/repos/${args.owner}/${args.repo}/issues`,
          {
            method: "POST",
            headers: {
              ...authHeaders,
              "Content-Type": "application/json",
              Accept: "application/vnd.github+json",
            },
            body: JSON.stringify({
              title: task.title,
              body: task.body,
              labels: task.labels || [],
              assignees: task.assignees || [],
              milestone: task.milestone,
            }),
          },
        );

        if (!response.ok) {
          const error = await response.text();
          throw new Error(`GitHub API error: ${response.status} ${error}`);
        }

        return await response.json();
      });

      createdIssues.push({
        number: issueData.number,
        url: issueData.html_url,
        title: issueData.title,
      });
    }

    return {
      success: true,
      created: createdIssues.length,
      issues: createdIssues,
    };
  }

  /**
   * Create a pull request
   */
  async createPR(args: CreatePRArgs): Promise<CreatePRResult> {
    const authHeaders = this.credentialVault.getAuthHeader("github");
    if (!authHeaders) {
      throw new Error("GitHub credentials not configured");
    }

    const prData = await this.retryHandler.execute(async () => {
      const response = await fetch(
        `${this.baseUrl}/repos/${args.owner}/${args.repo}/pulls`,
        {
          method: "POST",
          headers: {
            ...authHeaders,
            "Content-Type": "application/json",
            Accept: "application/vnd.github+json",
          },
          body: JSON.stringify({
            title: args.title,
            head: args.head,
            base: args.base,
            body: args.body || "",
            draft: args.draft || false,
          }),
        },
      );

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`GitHub API error: ${response.status} ${error}`);
      }

      return await response.json();
    });

    // Add labels if provided
    if (args.labels && args.labels.length > 0) {
      await this.addLabelsToPR(
        args.owner,
        args.repo,
        prData.number,
        args.labels,
      );
    }

    // Request reviews if provided
    if (args.reviewers && args.reviewers.length > 0) {
      await this.requestPRReviews(
        args.owner,
        args.repo,
        prData.number,
        args.reviewers,
      );
    }

    return {
      success: true,
      pr_number: prData.number,
      url: prData.html_url,
    };
  }

  /**
   * Review a pull request (simplified - would integrate with code review agent)
   */
  async reviewPR(args: ReviewPRArgs): Promise<ReviewPRResult> {
    const authHeaders = this.credentialVault.getAuthHeader("github");
    if (!authHeaders) {
      throw new Error("GitHub credentials not configured");
    }

    // Get PR details
    const cacheKey = `pr-${args.owner}-${args.repo}-${args.pr_number}`;
    let prData = this.cache.get(cacheKey);

    if (!prData) {
      prData = await this.retryHandler.execute(async () => {
        const response = await fetch(
          `${this.baseUrl}/repos/${args.owner}/${args.repo}/pulls/${args.pr_number}`,
          {
            headers: {
              ...authHeaders,
              Accept: "application/vnd.github+json",
            },
          },
        );

        if (!response.ok) {
          throw new Error(`GitHub API error: ${response.status}`);
        }

        return await response.json();
      });

      this.cache.set(cacheKey, prData, undefined, 60000); // Cache for 1 minute
    }

    // Get PR files
    const files = await this.getPRFiles(args.owner, args.repo, args.pr_number);

    // Perform review (simplified - in production, would use code review agent)
    const issues = [];
    let score = 100;

    // Example: Check for common issues
    for (const file of files) {
      if (file.patch) {
        // Simple checks (in production, use proper code analysis)
        if (file.patch.includes("console.log")) {
          issues.push({
            severity: "low" as const,
            file: file.filename,
            line: 1,
            message: "Remove console.log statements",
            suggestion: "Use proper logging",
          });
          score -= 1;
        }
      }
    }

    return {
      success: true,
      review: {
        summary: `Reviewed ${files.length} files, found ${issues.length} issues`,
        issues,
        score: Math.max(0, score),
      },
    };
  }

  /**
   * Update an issue
   */
  async updateIssue(
    owner: string,
    repo: string,
    issueNumber: number,
    updates: {
      state?: "open" | "closed";
      labels?: string[];
      assignees?: string[];
      milestone?: number;
      body?: string;
    },
  ): Promise<{ success: boolean }> {
    const authHeaders = this.credentialVault.getAuthHeader("github");
    if (!authHeaders) {
      throw new Error("GitHub credentials not configured");
    }

    await this.retryHandler.execute(async () => {
      const response = await fetch(
        `${this.baseUrl}/repos/${owner}/${repo}/issues/${issueNumber}`,
        {
          method: "PATCH",
          headers: {
            ...authHeaders,
            "Content-Type": "application/json",
            Accept: "application/vnd.github+json",
          },
          body: JSON.stringify(updates),
        },
      );

      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status}`);
      }
    });

    return { success: true };
  }

  /**
   * List issues
   */
  async listIssues(
    owner: string,
    repo: string,
    filters: {
      state?: "open" | "closed" | "all";
      labels?: string;
      assignee?: string;
      limit?: number;
    } = {},
  ): Promise<{
    issues: Array<{
      number: number;
      title: string;
      state: string;
      labels: string[];
    }>;
  }> {
    const authHeaders = this.credentialVault.getAuthHeader("github");
    if (!authHeaders) {
      throw new Error("GitHub credentials not configured");
    }

    const params = new URLSearchParams();
    if (filters.state) params.append("state", filters.state);
    if (filters.labels) params.append("labels", filters.labels);
    if (filters.assignee) params.append("assignee", filters.assignee);
    params.append("per_page", String(filters.limit || 30));

    const cacheKey = `issues-${owner}-${repo}-${params.toString()}`;
    let issues = this.cache.get<Array<unknown>>(cacheKey);

    if (!issues) {
      issues = await this.retryHandler.execute(async () => {
        const response = await fetch(
          `${this.baseUrl}/repos/${owner}/${repo}/issues?${params}`,
          {
            headers: {
              ...authHeaders,
              Accept: "application/vnd.github+json",
            },
          },
        );

        if (!response.ok) {
          throw new Error(`GitHub API error: ${response.status}`);
        }

        return await response.json();
      });

      this.cache.set(cacheKey, issues);
    }

    return {
      issues: issues.map((issue: any) => ({
        number: issue.number,
        title: issue.title,
        state: issue.state,
        labels: issue.labels.map((l: any) => l.name),
      })),
    };
  }

  /**
   * Helper: Add labels to PR
   */
  private async addLabelsToPR(
    owner: string,
    repo: string,
    prNumber: number,
    labels: string[],
  ): Promise<void> {
    const authHeaders = this.credentialVault.getAuthHeader("github");
    await fetch(
      `${this.baseUrl}/repos/${owner}/${repo}/issues/${prNumber}/labels`,
      {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ labels }),
      },
    );
  }

  /**
   * Helper: Request PR reviews
   */
  private async requestPRReviews(
    owner: string,
    repo: string,
    prNumber: number,
    reviewers: string[],
  ): Promise<void> {
    const authHeaders = this.credentialVault.getAuthHeader("github");
    await fetch(
      `${this.baseUrl}/repos/${owner}/${repo}/pulls/${prNumber}/requested_reviewers`,
      {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ reviewers }),
      },
    );
  }

  /**
   * Helper: Get PR files
   */
  private async getPRFiles(
    owner: string,
    repo: string,
    prNumber: number,
  ): Promise<Array<{ filename: string; patch?: string }>> {
    const authHeaders = this.credentialVault.getAuthHeader("github");
    const response = await fetch(
      `${this.baseUrl}/repos/${owner}/${repo}/pulls/${prNumber}/files`,
      {
        headers: {
          ...authHeaders,
          Accept: "application/vnd.github+json",
        },
      },
    );

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status}`);
    }

    return await response.json();
  }
}
