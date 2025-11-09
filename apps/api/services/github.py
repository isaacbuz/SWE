"""
GitHub API service wrapper for fetching PR and issue details.
Uses the existing GitHub integration package with rate limiting and caching.
"""
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import sys
import os

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from packages.integrations.github.client import GitHubClient
from packages.integrations.github.issues import IssueOperations
from packages.integrations.github.prs import PullRequestOperations

logger = logging.getLogger(__name__)


class GitHubAPIService:
    """GitHub API service wrapper with rate limiting and caching"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API service
        
        Args:
            token: GitHub personal access token (optional, can be set via env)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.warning("No GitHub token provided. GitHub API calls will fail.")
        
        self.client = GitHubClient(token=self.token) if self.token else None
        self.issues = IssueOperations(self.client) if self.client else None
        self.prs = PullRequestOperations(self.client) if self.client else None
    
    def _parse_github_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse GitHub URL to extract owner, repo, and number
        
        Args:
            url: GitHub URL (issue or PR)
            
        Returns:
            Dict with owner, repo, and number, or None if invalid
        """
        try:
            parsed = urlparse(url)
            if parsed.hostname not in ["github.com", "www.github.com"]:
                return None
            
            parts = parsed.path.strip("/").split("/")
            if len(parts) < 3:
                return None
            
            owner = parts[0]
            repo = parts[1]
            
            # Check if it's an issue or PR
            if "issues" in parts:
                idx = parts.index("issues")
                if idx + 1 < len(parts):
                    number = int(parts[idx + 1])
                    return {"owner": owner, "repo": repo, "number": number, "type": "issue"}
            elif "pull" in parts:
                idx = parts.index("pull")
                if idx + 1 < len(parts):
                    number = int(parts[idx + 1])
                    return {"owner": owner, "repo": repo, "number": number, "type": "pr"}
            
            return None
        except (ValueError, IndexError, AttributeError) as e:
            logger.error(f"Failed to parse GitHub URL {url}: {e}")
            return None
    
    async def get_issue_details(self, issue_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch issue details from GitHub API
        
        Args:
            issue_url: GitHub issue URL
            
        Returns:
            Issue details dict or None if not found
        """
        if not self.issues:
            logger.warning("GitHub client not initialized. Cannot fetch issue details.")
            return None
        
        parsed = self._parse_github_url(issue_url)
        if not parsed or parsed["type"] != "issue":
            return None
        
        try:
            # Use the existing GitHub client to fetch issue
            endpoint = f"/repos/{parsed['owner']}/{parsed['repo']}/issues/{parsed['number']}"
            issue_data = await self.client.get(endpoint)
            
            return {
                "title": issue_data.get("title"),
                "description": issue_data.get("body"),
                "author": issue_data.get("user", {}).get("login"),
                "state": issue_data.get("state"),
                "labels": [label.get("name") for label in issue_data.get("labels", [])],
                "number": issue_data.get("number"),
                "url": issue_data.get("html_url"),
                "created_at": issue_data.get("created_at"),
                "updated_at": issue_data.get("updated_at")
            }
        except Exception as e:
            logger.error(f"Failed to fetch issue details from GitHub: {e}")
            return None
    
    async def get_pr_details(self, pr_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch PR details from GitHub API
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            PR details dict or None if not found
        """
        if not self.prs:
            logger.warning("GitHub client not initialized. Cannot fetch PR details.")
            return None
        
        parsed = self._parse_github_url(pr_url)
        if not parsed or parsed["type"] != "pr":
            return None
        
        try:
            pr_data = await self.prs.get_pull_request(
                owner=parsed["owner"],
                repo=parsed["repo"],
                pull_number=parsed["number"]
            )
            
            return {
                "title": pr_data.get("title"),
                "description": pr_data.get("body"),
                "author": pr_data.get("user", {}).get("login"),
                "state": pr_data.get("state"),
                "merged": pr_data.get("merged", False),
                "number": pr_data.get("number"),
                "url": pr_data.get("html_url"),
                "created_at": pr_data.get("created_at"),
                "updated_at": pr_data.get("updated_at"),
                "head": {
                    "ref": pr_data.get("head", {}).get("ref"),
                    "sha": pr_data.get("head", {}).get("sha")
                },
                "base": {
                    "ref": pr_data.get("base", {}).get("ref"),
                    "sha": pr_data.get("base", {}).get("sha")
                }
            }
        except Exception as e:
            logger.error(f"Failed to fetch PR details from GitHub: {e}")
            return None
    
    async def validate_repository(self, repo_url: str) -> bool:
        """
        Validate that repository exists and is accessible
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            True if repository exists and is accessible
        """
        if not self.client:
            logger.warning("GitHub client not initialized. Cannot validate repository.")
            return False
        
        try:
            parsed = urlparse(repo_url)
            if parsed.hostname not in ["github.com", "www.github.com"]:
                return False
            
            parts = parsed.path.strip("/").split("/")
            if len(parts) < 2:
                return False
            
            owner = parts[0]
            repo = parts[1].replace(".git", "")
            
            # Try to fetch repository info
            endpoint = f"/repos/{owner}/{repo}"
            await self.client.get(endpoint)
            return True
        except Exception as e:
            logger.error(f"Failed to validate repository {repo_url}: {e}")
            return False


# Singleton instance
_github_service: Optional[GitHubAPIService] = None


def get_github_service(token: Optional[str] = None) -> GitHubAPIService:
    """
    Get or create GitHub API service instance
    
    Args:
        token: Optional GitHub token (uses env var if not provided)
        
    Returns:
        GitHubAPIService instance
    """
    global _github_service
    
    if _github_service is None:
        _github_service = GitHubAPIService(token=token)
    
    return _github_service

