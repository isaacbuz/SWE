"""
Activities for GitHub operations

These activities handle interactions with GitHub API,
including creating PRs, issues, branches, and updating statuses.
"""

from temporalio import activity
from typing import List, Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


@activity.defn
async def create_branch(branch_name: str, base: str = "main") -> Dict[str, Any]:
    """
    Create a new Git branch

    Args:
        branch_name: Name of the branch to create
        base: Base branch to branch from

    Returns:
        Branch information
    """
    logger.info(f"Creating branch: {branch_name} from {base}")

    # Simulate Git operation
    await asyncio.sleep(0.5)

    return {
        'name': branch_name,
        'base': base,
        'sha': 'abc123def456',
    }


@activity.defn
async def create_pull_request(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a GitHub pull request

    Args:
        pr_data: PR data including branch, title, description, etc.

    Returns:
        PR information including number and URL
    """
    logger.info(f"Creating PR: {pr_data.get('title')}")

    # Simulate GitHub API call
    await asyncio.sleep(1)

    pr_number = 123  # In production, this would be from GitHub API
    pr_url = f"https://github.com/org/repo/pull/{pr_number}"

    result = {
        'pr_number': pr_number,
        'pr_url': pr_url,
        'branch_name': pr_data['branch'],
        'files_changed': [],
        'test_results': {},
        'qa_score': 95.0,
        'merged': False,
    }

    logger.info(f"PR created: {pr_url}")
    return result


@activity.defn
async def merge_pull_request(pr_number: int) -> Dict[str, Any]:
    """
    Merge a GitHub pull request

    Args:
        pr_number: PR number to merge

    Returns:
        Merge information
    """
    logger.info(f"Merging PR #{pr_number}")

    # Simulate GitHub API call
    await asyncio.sleep(1)

    return {
        'pr_number': pr_number,
        'sha': 'merged123abc',
        'merged': True,
    }


@activity.defn
async def create_issue(issue_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a GitHub issue

    Args:
        issue_data: Issue data including title, body, labels

    Returns:
        Issue information
    """
    logger.info(f"Creating issue: {issue_data.get('title')}")

    # Simulate GitHub API call
    await asyncio.sleep(0.5)

    issue_number = 456
    issue_url = f"https://github.com/org/repo/issues/{issue_number}"

    logger.info(f"Issue created: {issue_url}")

    return {
        'issue_number': issue_number,
        'issue_url': issue_url,
    }


@activity.defn
async def update_pr_status(
    pr_number: int,
    state: str,
    description: str,
) -> None:
    """
    Update PR status check

    Args:
        pr_number: PR number
        state: Status state (pending, success, failure)
        description: Status description
    """
    logger.info(f"Updating PR #{pr_number} status to {state}: {description}")

    # Simulate GitHub API call
    await asyncio.sleep(0.3)

    logger.info("PR status updated")


@activity.defn
async def add_pr_comment(pr_number: int, comment: str) -> None:
    """
    Add a comment to a PR

    Args:
        pr_number: PR number
        comment: Comment text
    """
    logger.info(f"Adding comment to PR #{pr_number}")

    # Simulate GitHub API call
    await asyncio.sleep(0.3)

    logger.info("Comment added")


@activity.defn
async def get_pr_files(pr_number: int) -> List[Dict[str, Any]]:
    """
    Get files changed in a PR

    Args:
        pr_number: PR number

    Returns:
        List of changed files
    """
    logger.info(f"Fetching files for PR #{pr_number}")

    # Simulate GitHub API call
    await asyncio.sleep(0.5)

    return [
        {
            'filename': 'src/main.py',
            'status': 'modified',
            'additions': 50,
            'deletions': 10,
        },
        {
            'filename': 'tests/test_main.py',
            'status': 'added',
            'additions': 30,
            'deletions': 0,
        },
    ]


@activity.defn
async def add_pr_labels(pr_number: int, labels: List[str]) -> None:
    """
    Add labels to a PR

    Args:
        pr_number: PR number
        labels: List of label names
    """
    logger.info(f"Adding labels to PR #{pr_number}: {labels}")

    # Simulate GitHub API call
    await asyncio.sleep(0.3)

    logger.info("Labels added")


@activity.defn
async def request_pr_review(pr_number: int, reviewers: List[str]) -> None:
    """
    Request PR review from users

    Args:
        pr_number: PR number
        reviewers: List of GitHub usernames
    """
    logger.info(f"Requesting review for PR #{pr_number} from {reviewers}")

    # Simulate GitHub API call
    await asyncio.sleep(0.3)

    logger.info("Review requested")


@activity.defn
async def get_commit_status(sha: str) -> Dict[str, Any]:
    """
    Get status of a commit

    Args:
        sha: Commit SHA

    Returns:
        Commit status information
    """
    logger.info(f"Fetching status for commit {sha}")

    # Simulate GitHub API call
    await asyncio.sleep(0.3)

    return {
        'state': 'success',
        'statuses': [
            {'context': 'ci/tests', 'state': 'success'},
            {'context': 'ci/lint', 'state': 'success'},
        ],
    }


@activity.defn
async def create_release(
    tag: str,
    name: str,
    body: str,
    draft: bool = False,
) -> Dict[str, Any]:
    """
    Create a GitHub release

    Args:
        tag: Release tag
        name: Release name
        body: Release notes
        draft: Whether release is a draft

    Returns:
        Release information
    """
    logger.info(f"Creating release: {tag}")

    # Simulate GitHub API call
    await asyncio.sleep(0.5)

    release_url = f"https://github.com/org/repo/releases/tag/{tag}"

    logger.info(f"Release created: {release_url}")

    return {
        'tag': tag,
        'url': release_url,
        'draft': draft,
    }


@activity.defn
async def close_issue(issue_number: int, comment: Optional[str] = None) -> None:
    """
    Close a GitHub issue

    Args:
        issue_number: Issue number to close
        comment: Optional closing comment
    """
    logger.info(f"Closing issue #{issue_number}")

    if comment:
        await add_issue_comment(issue_number, comment)

    # Simulate GitHub API call
    await asyncio.sleep(0.3)

    logger.info("Issue closed")


@activity.defn
async def add_issue_comment(issue_number: int, comment: str) -> None:
    """
    Add a comment to an issue

    Args:
        issue_number: Issue number
        comment: Comment text
    """
    logger.info(f"Adding comment to issue #{issue_number}")

    # Simulate GitHub API call
    await asyncio.sleep(0.3)

    logger.info("Comment added to issue")


@activity.defn
async def get_open_prs(repository: str) -> List[Dict[str, Any]]:
    """
    Get all open PRs in a repository

    Args:
        repository: Repository name

    Returns:
        List of open PRs
    """
    logger.info(f"Fetching open PRs for {repository}")

    # Simulate GitHub API call
    await asyncio.sleep(0.5)

    return [
        {
            'number': 123,
            'title': 'Add feature X',
            'branch': 'feature/x',
            'author': 'user1',
        },
        {
            'number': 124,
            'title': 'Fix bug Y',
            'branch': 'bugfix/y',
            'author': 'user2',
        },
    ]


@activity.defn
async def sync_branch(branch: str, base: str = "main") -> None:
    """
    Sync a branch with its base branch

    Args:
        branch: Branch to sync
        base: Base branch to sync from
    """
    logger.info(f"Syncing {branch} with {base}")

    # Simulate Git operation
    await asyncio.sleep(0.5)

    logger.info("Branch synced")


@activity.defn
async def create_commit(
    branch: str,
    files: Dict[str, str],
    message: str,
) -> str:
    """
    Create a commit with file changes

    Args:
        branch: Branch to commit to
        files: Dictionary of filename -> content
        message: Commit message

    Returns:
        Commit SHA
    """
    logger.info(f"Creating commit on {branch}: {message}")

    # Simulate Git operation
    await asyncio.sleep(0.5)

    commit_sha = "commit123abc"

    logger.info(f"Commit created: {commit_sha}")
    return commit_sha


@activity.defn
async def push_branch(branch: str, force: bool = False) -> None:
    """
    Push a branch to remote

    Args:
        branch: Branch to push
        force: Whether to force push
    """
    logger.info(f"Pushing branch {branch}{' (force)' if force else ''}")

    # Simulate Git operation
    await asyncio.sleep(0.5)

    logger.info("Branch pushed")
