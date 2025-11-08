"""
GitHub Webhooks Handler

Provides webhook handling:
- Webhook signature verification
- Event parsing
- Event routing
- Webhook management
"""

import hashlib
import hmac
import json
from typing import Any, Callable, Dict, List, Optional

from .client import GitHubClient


class WebhookHandler:
    """
    GitHub Webhooks handler

    Handles webhook event verification, parsing, and routing.
    """

    def __init__(
        self,
        secret: str,
        client: Optional[GitHubClient] = None,
    ):
        """
        Initialize webhook handler

        Args:
            secret: Webhook secret for signature verification
            client: Optional GitHubClient for webhook management
        """
        self.secret = secret
        self.client = client
        self.event_handlers: Dict[str, List[Callable]] = {}

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature

        Args:
            payload: Raw webhook payload bytes
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid
        """
        return GitHubClient.verify_webhook_signature(payload, signature, self.secret)

    def parse_event(
        self,
        payload: bytes,
        event_type: str,
        signature: str,
    ) -> Dict[str, Any]:
        """
        Parse and verify webhook event

        Args:
            payload: Raw webhook payload bytes
            event_type: X-GitHub-Event header value
            signature: X-Hub-Signature-256 header value

        Returns:
            Parsed event data

        Raises:
            ValueError: If signature is invalid
        """
        # Verify signature
        if not self.verify_signature(payload, signature):
            raise ValueError("Invalid webhook signature")

        # Parse JSON
        data = json.loads(payload.decode("utf-8"))

        return {
            "event_type": event_type,
            "data": data,
            "action": data.get("action"),
        }

    def on_event(self, event_type: str):
        """
        Decorator to register event handler

        Usage:
            @handler.on_event("issues")
            async def handle_issues(event):
                ...

        Args:
            event_type: GitHub event type (e.g., "issues", "pull_request")
        """
        def decorator(func: Callable):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func

        return decorator

    async def handle_event(
        self,
        payload: bytes,
        event_type: str,
        signature: str,
    ) -> List[Any]:
        """
        Handle incoming webhook event

        Args:
            payload: Raw webhook payload bytes
            event_type: X-GitHub-Event header value
            signature: X-Hub-Signature-256 header value

        Returns:
            List of handler results
        """
        # Parse and verify event
        event = self.parse_event(payload, event_type, signature)

        # Get handlers for this event type
        handlers = self.event_handlers.get(event_type, [])

        # Execute handlers
        results = []
        for handler in handlers:
            result = await handler(event)
            results.append(result)

        return results

    # Webhook Management API methods (requires client)

    async def create_webhook(
        self,
        owner: str,
        repo: str,
        url: str,
        events: Optional[List[str]] = None,
        active: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a repository webhook

        Args:
            owner: Repository owner
            repo: Repository name
            url: Webhook URL
            events: List of events to subscribe to
            active: Whether webhook is active

        Returns:
            Created webhook data
        """
        if not self.client:
            raise ValueError("Client required for webhook management")

        if events is None:
            events = ["push", "pull_request", "issues"]

        endpoint = f"/repos/{owner}/{repo}/hooks"
        payload = {
            "name": "web",
            "active": active,
            "events": events,
            "config": {
                "url": url,
                "content_type": "json",
                "secret": self.secret,
                "insecure_ssl": "0",
            },
        }

        return await self.client.post(endpoint, json=payload)

    async def list_webhooks(
        self,
        owner: str,
        repo: str,
    ) -> List[Dict[str, Any]]:
        """
        List repository webhooks

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of webhooks
        """
        if not self.client:
            raise ValueError("Client required for webhook management")

        endpoint = f"/repos/{owner}/{repo}/hooks"
        return await self.client.get(endpoint)

    async def get_webhook(
        self,
        owner: str,
        repo: str,
        hook_id: int,
    ) -> Dict[str, Any]:
        """
        Get webhook details

        Args:
            owner: Repository owner
            repo: Repository name
            hook_id: Webhook ID

        Returns:
            Webhook data
        """
        if not self.client:
            raise ValueError("Client required for webhook management")

        endpoint = f"/repos/{owner}/{repo}/hooks/{hook_id}"
        return await self.client.get(endpoint)

    async def update_webhook(
        self,
        owner: str,
        repo: str,
        hook_id: int,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update a webhook

        Args:
            owner: Repository owner
            repo: Repository name
            hook_id: Webhook ID
            url: New webhook URL
            events: New events list
            active: New active status

        Returns:
            Updated webhook data
        """
        if not self.client:
            raise ValueError("Client required for webhook management")

        endpoint = f"/repos/{owner}/{repo}/hooks/{hook_id}"
        payload = {}

        if url is not None:
            payload["config"] = {"url": url, "content_type": "json", "secret": self.secret}
        if events is not None:
            payload["events"] = events
        if active is not None:
            payload["active"] = active

        return await self.client.patch(endpoint, json=payload)

    async def delete_webhook(
        self,
        owner: str,
        repo: str,
        hook_id: int,
    ) -> Dict[str, Any]:
        """
        Delete a webhook

        Args:
            owner: Repository owner
            repo: Repository name
            hook_id: Webhook ID

        Returns:
            Empty dict on success
        """
        if not self.client:
            raise ValueError("Client required for webhook management")

        endpoint = f"/repos/{owner}/{repo}/hooks/{hook_id}"
        return await self.client.delete(endpoint)

    async def ping_webhook(
        self,
        owner: str,
        repo: str,
        hook_id: int,
    ) -> Dict[str, Any]:
        """
        Ping a webhook

        Args:
            owner: Repository owner
            repo: Repository name
            hook_id: Webhook ID

        Returns:
            Empty dict on success
        """
        if not self.client:
            raise ValueError("Client required for webhook management")

        endpoint = f"/repos/{owner}/{repo}/hooks/{hook_id}/pings"
        return await self.client.post(endpoint)

    async def test_webhook(
        self,
        owner: str,
        repo: str,
        hook_id: int,
    ) -> Dict[str, Any]:
        """
        Test a webhook

        Args:
            owner: Repository owner
            repo: Repository name
            hook_id: Webhook ID

        Returns:
            Empty dict on success
        """
        if not self.client:
            raise ValueError("Client required for webhook management")

        endpoint = f"/repos/{owner}/{repo}/hooks/{hook_id}/tests"
        return await self.client.post(endpoint)


# Event type constants
class GitHubEvents:
    """GitHub webhook event types"""

    PUSH = "push"
    PULL_REQUEST = "pull_request"
    PULL_REQUEST_REVIEW = "pull_request_review"
    PULL_REQUEST_REVIEW_COMMENT = "pull_request_review_comment"
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    CREATE = "create"
    DELETE = "delete"
    FORK = "fork"
    GOLLUM = "gollum"  # Wiki
    RELEASE = "release"
    STATUS = "status"
    WATCH = "watch"
    WORKFLOW_RUN = "workflow_run"
    WORKFLOW_JOB = "workflow_job"
    CHECK_RUN = "check_run"
    CHECK_SUITE = "check_suite"
    DEPLOYMENT = "deployment"
    DEPLOYMENT_STATUS = "deployment_status"
    REPOSITORY = "repository"
    ORGANIZATION = "organization"
    MEMBER = "member"
    TEAM = "team"


# Example webhook handler implementation
class ExampleWebhookHandlers:
    """Example webhook handlers for common events"""

    def __init__(self, handler: WebhookHandler):
        self.handler = handler
        self._register_handlers()

    def _register_handlers(self):
        """Register example handlers"""
        self.handler.on_event(GitHubEvents.ISSUES)(self.handle_issue)
        self.handler.on_event(GitHubEvents.PULL_REQUEST)(self.handle_pr)
        self.handler.on_event(GitHubEvents.PUSH)(self.handle_push)

    async def handle_issue(self, event: Dict[str, Any]):
        """Handle issue events"""
        action = event["action"]
        issue = event["data"]["issue"]

        print(f"Issue {action}: {issue['title']}")

        if action == "opened":
            # Handle new issue
            pass
        elif action == "closed":
            # Handle closed issue
            pass

        return {"handled": "issue", "action": action}

    async def handle_pr(self, event: Dict[str, Any]):
        """Handle pull request events"""
        action = event["action"]
        pr = event["data"]["pull_request"]

        print(f"PR {action}: {pr['title']}")

        if action == "opened":
            # Handle new PR
            pass
        elif action == "closed" and pr.get("merged"):
            # Handle merged PR
            pass

        return {"handled": "pull_request", "action": action}

    async def handle_push(self, event: Dict[str, Any]):
        """Handle push events"""
        ref = event["data"]["ref"]
        commits = event["data"]["commits"]

        print(f"Push to {ref}: {len(commits)} commits")

        return {"handled": "push", "commits": len(commits)}
