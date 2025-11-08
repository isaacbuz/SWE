"""
GitHub Integration Package

Provides comprehensive GitHub API integration including:
- Issue operations
- Pull request management
- Project board operations
- GitHub Actions integration
- Webhook handling
"""

from .client import GitHubClient
from .issues import IssueOperations
from .prs import PullRequestOperations
from .projects import ProjectOperations
from .actions import ActionsOperations
from .webhooks import WebhookHandler

__all__ = [
    "GitHubClient",
    "IssueOperations",
    "PullRequestOperations",
    "ProjectOperations",
    "ActionsOperations",
    "WebhookHandler",
]
