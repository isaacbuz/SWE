#!/usr/bin/env python3
"""
Fetch GitHub Issues, PRs, Actions, and Epics
"""
import os
import json
import sys
from typing import Dict, List, Any
from datetime import datetime

try:
    from packages.integrations.github.client import GitHubClient
    from packages.integrations.github.issues import IssueOperations
    from packages.integrations.github.prs import PROperations
except ImportError:
    print("Warning: GitHub integration not available, using fallback")
    GitHubClient = None
    IssueOperations = None
    PROperations = None


def fetch_with_gh_cli() -> Dict[str, Any]:
    """Fallback: Use GitHub CLI if available"""
    import subprocess
    
    try:
        # Fetch issues
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", "isaacbuz/SWE", "--state", "all", "--json", "number,title,state,labels,assignees,createdAt,updatedAt,body"],
            capture_output=True,
            text=True,
            check=True
        )
        issues = json.loads(result.stdout)
        
        # Fetch PRs
        pr_result = subprocess.run(
            ["gh", "pr", "list", "--repo", "isaacbuz/SWE", "--state", "all", "--json", "number,title,state,labels,assignees,createdAt,updatedAt,body"],
            capture_output=True,
            text=True,
            check=True
        )
        prs = json.loads(pr_result.stdout)
        
        return {
            "issues": issues,
            "pull_requests": prs,
            "fetched_at": datetime.now().isoformat()
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"error": "GitHub CLI not available"}


async def fetch_with_api() -> Dict[str, Any]:
    """Fetch using GitHub API client"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {"error": "GITHUB_TOKEN not set"}
    
    client = GitHubClient(token=token)
    issues_ops = IssueOperations(client)
    
    # Fetch all open issues
    open_issues = await issues_ops.list_issues(
        owner="isaacbuz",
        repo="SWE",
        state="open",
        per_page=100
    )
    
    # Fetch all closed issues
    closed_issues = await issues_ops.list_issues(
        owner="isaacbuz",
        repo="SWE",
        state="closed",
        per_page=100
    )
    
    # Fetch PRs (issues with pull_request field)
    all_issues = open_issues + closed_issues
    prs = [issue for issue in all_issues if "pull_request" in issue]
    issues_only = [issue for issue in all_issues if "pull_request" not in issue]
    
    return {
        "issues": issues_only,
        "pull_requests": prs,
        "total_open": len(open_issues),
        "total_closed": len(closed_issues),
        "fetched_at": datetime.now().isoformat()
    }


def main():
    """Main entry point"""
    output_file = sys.argv[1] if len(sys.argv) > 1 else ".github/issues-data.json"
    
    # Try API first, fallback to CLI
    if GitHubClient:
        import asyncio
        data = asyncio.run(fetch_with_api())
    else:
        data = fetch_with_gh_cli()
    
    # Save to file
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Fetched {len(data.get('issues', []))} issues and {len(data.get('pull_requests', []))} PRs")
    print(f"📁 Saved to {output_file}")
    
    return data


if __name__ == "__main__":
    main()

