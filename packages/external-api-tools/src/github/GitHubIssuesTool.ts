/**
 * GitHub Issues Tool Wrapper
 * 
 * Provides tools for managing GitHub issues.
 */
import { GitHubToolWrapper } from './GitHubToolWrapper';
import { ToolSpec } from '@ai-company/openapi-tools';

export class GitHubIssuesTool {
  private github: GitHubToolWrapper;

  constructor(github: GitHubToolWrapper) {
    this.github = github;
  }

  /**
   * Get tool specs for GitHub Issues operations
   */
  getToolSpecs(): ToolSpec[] {
    return [
      {
        name: 'github_create_issue',
        description: 'Create a new GitHub issue',
        jsonSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: 'Repository owner' },
            repo: { type: 'string', description: 'Repository name' },
            title: { type: 'string', description: 'Issue title' },
            body: { type: 'string', description: 'Issue body/description' },
            labels: {
              type: 'array',
              items: { type: 'string' },
              description: 'Labels to apply to the issue',
            },
            assignees: {
              type: 'array',
              items: { type: 'string' },
              description: 'Usernames to assign to the issue',
            },
            milestone: { type: 'number', description: 'Milestone number' },
          },
          required: ['owner', 'repo', 'title'],
        },
      },
      {
        name: 'github_list_issues',
        description: 'List GitHub issues for a repository',
        jsonSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: 'Repository owner' },
            repo: { type: 'string', description: 'Repository name' },
            state: {
              type: 'string',
              enum: ['open', 'closed', 'all'],
              description: 'Filter by issue state',
            },
            labels: {
              type: 'array',
              items: { type: 'string' },
              description: 'Filter by labels',
            },
            assignee: { type: 'string', description: 'Filter by assignee' },
            creator: { type: 'string', description: 'Filter by creator' },
            milestone: { type: 'string', description: 'Filter by milestone' },
            sort: {
              type: 'string',
              enum: ['created', 'updated', 'comments'],
              description: 'Sort field',
            },
            direction: {
              type: 'string',
              enum: ['asc', 'desc'],
              description: 'Sort direction',
            },
            per_page: { type: 'number', description: 'Results per page' },
            page: { type: 'number', description: 'Page number' },
          },
          required: ['owner', 'repo'],
        },
      },
      {
        name: 'github_get_issue',
        description: 'Get a specific GitHub issue',
        jsonSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: 'Repository owner' },
            repo: { type: 'string', description: 'Repository name' },
            issue_number: { type: 'number', description: 'Issue number' },
          },
          required: ['owner', 'repo', 'issue_number'],
        },
      },
      {
        name: 'github_update_issue',
        description: 'Update a GitHub issue',
        jsonSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: 'Repository owner' },
            repo: { type: 'string', description: 'Repository name' },
            issue_number: { type: 'number', description: 'Issue number' },
            title: { type: 'string', description: 'New issue title' },
            body: { type: 'string', description: 'New issue body' },
            state: {
              type: 'string',
              enum: ['open', 'closed'],
              description: 'Issue state',
            },
            labels: {
              type: 'array',
              items: { type: 'string' },
              description: 'Labels to apply',
            },
            assignees: {
              type: 'array',
              items: { type: 'string' },
              description: 'Usernames to assign',
            },
            milestone: { type: 'number', description: 'Milestone number' },
          },
          required: ['owner', 'repo', 'issue_number'],
        },
      },
      {
        name: 'github_add_issue_comment',
        description: 'Add a comment to a GitHub issue',
        jsonSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: 'Repository owner' },
            repo: { type: 'string', description: 'Repository name' },
            issue_number: { type: 'number', description: 'Issue number' },
            body: { type: 'string', description: 'Comment body' },
          },
          required: ['owner', 'repo', 'issue_number', 'body'],
        },
      },
      {
        name: 'github_list_issue_comments',
        description: 'List comments for a GitHub issue',
        jsonSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: 'Repository owner' },
            repo: { type: 'string', description: 'Repository name' },
            issue_number: { type: 'number', description: 'Issue number' },
            per_page: { type: 'number', description: 'Results per page' },
            page: { type: 'number', description: 'Page number' },
          },
          required: ['owner', 'repo', 'issue_number'],
        },
      },
    ];
  }

  /**
   * Execute a GitHub Issues tool
   */
  async execute(toolName: string, args: any): Promise<any> {
    switch (toolName) {
      case 'github_create_issue':
        return this.github.createIssue(
          args.owner,
          args.repo,
          args.title,
          args.body,
          args.labels,
          args.assignees,
          args.milestone
        );

      case 'github_list_issues':
        return this.github.listIssues(
          args.owner,
          args.repo,
          {
            state: args.state,
            labels: args.labels,
            assignee: args.assignee,
            creator: args.creator,
            milestone: args.milestone,
            sort: args.sort,
            direction: args.direction,
            per_page: args.per_page,
            page: args.page,
          }
        );

      case 'github_get_issue':
        return this.github.getIssue(args.owner, args.repo, args.issue_number);

      case 'github_update_issue':
        return this.github.updateIssue(
          args.owner,
          args.repo,
          args.issue_number,
          {
            title: args.title,
            body: args.body,
            state: args.state,
            labels: args.labels,
            assignees: args.assignees,
            milestone: args.milestone,
          }
        );

      case 'github_add_issue_comment':
        return this.github.addIssueComment(
          args.owner,
          args.repo,
          args.issue_number,
          args.body
        );

      case 'github_list_issue_comments':
        return this.github.listIssueComments(
          args.owner,
          args.repo,
          args.issue_number,
          args.per_page,
          args.page
        );

      default:
        throw new Error(`Unknown tool: ${toolName}`);
    }
  }
}

