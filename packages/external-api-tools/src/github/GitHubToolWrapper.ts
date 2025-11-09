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

  // ========== Issues Operations ==========

  /**
   * Create a single issue
   */
  async createIssue(
    owner: string,
    repo: string,
    title: string,
    body?: string,
    labels?: string[],
    assignees?: string[],
    milestone?: number
  ): Promise<{ number: number; url: string; title: string }> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.issues.create({
      owner,
      repo,
      title,
      body,
      labels,
      assignees,
      milestone,
    });

    return {
      number: response.data.number,
      url: response.data.html_url,
      title: response.data.title,
    };
  }

  /**
   * List issues
   */
  async listIssues(
    owner: string,
    repo: string,
    options?: {
      state?: 'open' | 'closed' | 'all';
      labels?: string[];
      assignee?: string;
      creator?: string;
      milestone?: string;
      sort?: 'created' | 'updated' | 'comments';
      direction?: 'asc' | 'desc';
      per_page?: number;
      page?: number;
    }
  ): Promise<any[]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.issues.listForRepo({
      owner,
      repo,
      state: options?.state || 'open',
      labels: options?.labels?.join(','),
      assignee: options?.assignee,
      creator: options?.creator,
      milestone: options?.milestone,
      sort: options?.sort || 'created',
      direction: options?.direction || 'desc',
      per_page: options?.per_page || 30,
      page: options?.page || 1,
    });

    return response.data.map((issue) => ({
      number: issue.number,
      title: issue.title,
      state: issue.state,
      body: issue.body,
      labels: issue.labels.map((l: any) => l.name),
      assignees: issue.assignees.map((a: any) => a.login),
      created_at: issue.created_at,
      updated_at: issue.updated_at,
      url: issue.html_url,
    }));
  }

  /**
   * Get a specific issue
   */
  async getIssue(owner: string, repo: string, issueNumber: number): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.issues.get({
      owner,
      repo,
      issue_number: issueNumber,
    });

    return {
      number: response.data.number,
      title: response.data.title,
      state: response.data.state,
      body: response.data.body,
      labels: response.data.labels.map((l: any) => l.name),
      assignees: response.data.assignees.map((a: any) => a.login),
      created_at: response.data.created_at,
      updated_at: response.data.updated_at,
      url: response.data.html_url,
    };
  }

  /**
   * Update an issue (enhanced version)
   */
  async updateIssue(
    owner: string,
    repo: string,
    issueNumber: number,
    updates: {
      title?: string;
      body?: string;
      state?: 'open' | 'closed';
      labels?: string[];
      assignees?: string[];
      milestone?: number;
    }
  ): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.issues.update({
      owner,
      repo,
      issue_number: issueNumber,
      title: updates.title,
      body: updates.body,
      state: updates.state,
      labels: updates.labels,
      assignees: updates.assignees,
      milestone: updates.milestone,
    });

    return {
      number: response.data.number,
      title: response.data.title,
      state: response.data.state,
      url: response.data.html_url,
    };
  }

  /**
   * Add comment to issue
   */
  async addIssueComment(
    owner: string,
    repo: string,
    issueNumber: number,
    body: string
  ): Promise<{ id: number; url: string }> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.issues.createComment({
      owner,
      repo,
      issue_number: issueNumber,
      body,
    });

    return {
      id: response.data.id,
      url: response.data.html_url,
    };
  }

  /**
   * List issue comments
   */
  async listIssueComments(
    owner: string,
    repo: string,
    issueNumber: number,
    perPage?: number,
    page?: number
  ): Promise<any[]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.issues.listComments({
      owner,
      repo,
      issue_number: issueNumber,
      per_page: perPage || 30,
      page: page || 1,
    });

    return response.data.map((comment) => ({
      id: comment.id,
      body: comment.body,
      user: comment.user?.login,
      created_at: comment.created_at,
      updated_at: comment.updated_at,
      url: comment.html_url,
    }));
  }

  // ========== Pull Request Operations ==========

  /**
   * List pull requests
   */
  async listPRs(
    owner: string,
    repo: string,
    options?: {
      state?: 'open' | 'closed' | 'all';
      head?: string;
      base?: string;
      sort?: 'created' | 'updated' | 'popularity' | 'long-running';
      direction?: 'asc' | 'desc';
      per_page?: number;
      page?: number;
    }
  ): Promise<any[]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.pulls.list({
      owner,
      repo,
      state: options?.state || 'open',
      head: options?.head,
      base: options?.base,
      sort: options?.sort || 'created',
      direction: options?.direction || 'desc',
      per_page: options?.per_page || 30,
      page: options?.page || 1,
    });

    return response.data.map((pr) => ({
      number: pr.number,
      title: pr.title,
      state: pr.state,
      body: pr.body,
      head: pr.head.ref,
      base: pr.base.ref,
      labels: pr.labels.map((l: any) => l.name),
      created_at: pr.created_at,
      updated_at: pr.updated_at,
      url: pr.html_url,
    }));
  }

  /**
   * Get a specific pull request
   */
  async getPR(owner: string, repo: string, prNumber: number): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.pulls.get({
      owner,
      repo,
      pull_number: prNumber,
    });

    return {
      number: response.data.number,
      title: response.data.title,
      state: response.data.state,
      body: response.data.body,
      head: response.data.head.ref,
      base: response.data.base.ref,
      labels: response.data.labels.map((l: any) => l.name),
      created_at: response.data.created_at,
      updated_at: response.data.updated_at,
      url: response.data.html_url,
      mergeable: response.data.mergeable,
    };
  }

  /**
   * Update a pull request
   */
  async updatePR(
    owner: string,
    repo: string,
    prNumber: number,
    updates: {
      title?: string;
      body?: string;
      state?: 'open' | 'closed';
      base?: string;
    }
  ): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.pulls.update({
      owner,
      repo,
      pull_number: prNumber,
      title: updates.title,
      body: updates.body,
      base: updates.base,
    });

    return {
      number: response.data.number,
      title: response.data.title,
      state: response.data.state,
      url: response.data.html_url,
    };
  }

  /**
   * List PR reviews
   */
  async listPRReviews(
    owner: string,
    repo: string,
    prNumber: number
  ): Promise<any[]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.pulls.listReviews({
      owner,
      repo,
      pull_number: prNumber,
    });

    return response.data.map((review) => ({
      id: review.id,
      state: review.state,
      body: review.body,
      user: review.user?.login,
      submitted_at: review.submitted_at,
    }));
  }

  // ========== Projects Operations ==========

  /**
   * List organization projects
   */
  async listOrgProjects(org: string): Promise<any[]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.projects.listForOrg({
      org,
    });

    return response.data.map((project) => ({
      id: project.id,
      name: project.name,
      body: project.body,
      state: project.state,
      created_at: project.created_at,
      updated_at: project.updated_at,
    }));
  }

  /**
   * List repository projects
   */
  async listRepoProjects(owner: string, repo: string): Promise<any[]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.projects.listForRepo({
      owner,
      repo,
    });

    return response.data.map((project) => ({
      id: project.id,
      name: project.name,
      body: project.body,
      state: project.state,
      created_at: project.created_at,
      updated_at: project.updated_at,
    }));
  }

  /**
   * Get a project
   */
  async getProject(projectId: number): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.projects.get({
      project_id: projectId,
    });

    return {
      id: response.data.id,
      name: response.data.name,
      body: response.data.body,
      state: response.data.state,
      created_at: response.data.created_at,
      updated_at: response.data.updated_at,
    };
  }

  /**
   * Create a project
   */
  async createProject(
    owner: string,
    name: string,
    body?: string,
    isOrgProject: boolean = false
  ): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = isOrgProject
      ? await this.octokit.rest.projects.createForOrg({
          org: owner,
          name,
          body,
        })
      : await this.octokit.rest.projects.createForRepo({
          owner,
          repo: name, // Note: This is a simplification
          name,
          body,
        });

    return {
      id: response.data.id,
      name: response.data.name,
      body: response.data.body,
      state: response.data.state,
      url: response.data.html_url,
    };
  }

  /**
   * List project columns
   */
  async listProjectColumns(projectId: number): Promise<any[]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.projects.listColumns({
      project_id: projectId,
    });

    return response.data.map((column) => ({
      id: column.id,
      name: column.name,
      created_at: column.created_at,
      updated_at: column.updated_at,
    }));
  }

  /**
   * Add a card to a project column
   */
  async addProjectCard(
    columnId: number,
    contentId?: number,
    contentType?: 'Issue' | 'PullRequest',
    note?: string
  ): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.projects.createCard({
      column_id: columnId,
      content_id: contentId,
      content_type: contentType,
      note,
    });

    return {
      id: response.data.id,
      note: response.data.note,
      archived: response.data.archived,
    };
  }

  // ========== GitHub Actions Operations ==========

  /**
   * List workflows for a repository
   */
  async listWorkflows(owner: string, repo: string): Promise<any[]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.actions.listWorkflowsForRepo({
      owner,
      repo,
    });

    return response.data.workflows.map((workflow) => ({
      id: workflow.id,
      name: workflow.name,
      path: workflow.path,
      state: workflow.state,
      created_at: workflow.created_at,
      updated_at: workflow.updated_at,
      url: workflow.html_url,
    }));
  }

  /**
   * Get a workflow
   */
  async getWorkflow(owner: string, repo: string, workflowId: number): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.actions.getWorkflow({
      owner,
      repo,
      workflow_id: workflowId,
    });

    return {
      id: response.data.id,
      name: response.data.name,
      path: response.data.path,
      state: response.data.state,
      created_at: response.data.created_at,
      updated_at: response.data.updated_at,
      url: response.data.html_url,
    };
  }

  /**
   * List workflow runs
   */
  async listWorkflowRuns(
    owner: string,
    repo: string,
    workflowId?: number,
    options?: {
      actor?: string;
      branch?: string;
      event?: string;
      status?: 'completed' | 'action_required' | 'cancelled' | 'failure' | 'neutral' | 'skipped' | 'stale' | 'success' | 'timed_out' | 'in_progress' | 'queued' | 'requested' | 'waiting';
      per_page?: number;
      page?: number;
    }
  ): Promise<any[]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const params: any = {
      owner,
      repo,
      actor: options?.actor,
      branch: options?.branch,
      event: options?.event,
      status: options?.status,
      per_page: options?.per_page || 30,
      page: options?.page || 1,
    };

    if (workflowId) {
      params.workflow_id = workflowId;
    }

    const response = await this.octokit.rest.actions.listWorkflowRuns(params);

    return response.data.workflow_runs.map((run) => ({
      id: run.id,
      name: run.name,
      head_branch: run.head_branch,
      head_sha: run.head_sha,
      status: run.status,
      conclusion: run.conclusion,
      created_at: run.created_at,
      updated_at: run.updated_at,
      url: run.html_url,
    }));
  }

  /**
   * Get a workflow run
   */
  async getWorkflowRun(owner: string, repo: string, runId: number): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    const response = await this.octokit.rest.actions.getWorkflowRun({
      owner,
      repo,
      run_id: runId,
    });

    return {
      id: response.data.id,
      name: response.data.name,
      head_branch: response.data.head_branch,
      head_sha: response.data.head_sha,
      status: response.data.status,
      conclusion: response.data.conclusion,
      created_at: response.data.created_at,
      updated_at: response.data.updated_at,
      url: response.data.html_url,
    };
  }

  /**
   * Cancel a workflow run
   */
  async cancelWorkflowRun(owner: string, repo: string, runId: number): Promise<void> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    await this.octokit.rest.actions.cancelWorkflowRun({
      owner,
      repo,
      run_id: runId,
    });
  }

  /**
   * Re-run a workflow
   */
  async rerunWorkflow(owner: string, repo: string, runId: number): Promise<void> {
    await this.initialize();
    await this.rateLimiter.checkLimit('github');

    if (!this.octokit) {
      throw new Error('GitHub client not initialized');
    }

    await this.octokit.rest.actions.reRunWorkflow({
      owner,
      repo,
      run_id: runId,
    });
  }
}

