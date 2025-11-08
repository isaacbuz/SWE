"""
GitHub Actions Integration

Provides GitHub Actions operations:
- Trigger workflows
- Get workflow status
- Download artifacts
- Cancel runs
"""

import asyncio
from typing import Any, Dict, List, Optional

from .client import GitHubClient


class ActionsOperations:
    """
    GitHub Actions operations

    Handles workflow execution, monitoring, and artifact management.
    """

    def __init__(self, client: GitHubClient):
        """
        Initialize Actions operations

        Args:
            client: GitHubClient instance
        """
        self.client = client

    async def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Trigger a workflow dispatch event

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or filename (e.g., "main.yml")
            ref: Git ref (branch, tag, or SHA)
            inputs: Workflow inputs

        Returns:
            Empty dict on success
        """
        endpoint = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        payload = {"ref": ref}

        if inputs:
            payload["inputs"] = inputs

        return await self.client.post(endpoint, json=payload)

    async def get_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Get workflow details

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or filename

        Returns:
            Workflow data
        """
        endpoint = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}"
        return await self.client.get(endpoint)

    async def list_workflows(
        self,
        owner: str,
        repo: str,
    ) -> List[Dict[str, Any]]:
        """
        List repository workflows

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of workflows
        """
        endpoint = f"/repos/{owner}/{repo}/actions/workflows"
        response = await self.client.get(endpoint)
        return response.get("workflows", [])

    async def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: Optional[str] = None,
        branch: Optional[str] = None,
        event: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        List workflow runs

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Filter by workflow ID or filename
            branch: Filter by branch
            event: Filter by event type
            status: Filter by status (e.g., "completed", "in_progress")
            per_page: Results per page

        Returns:
            List of workflow runs
        """
        if workflow_id:
            endpoint = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            endpoint = f"/repos/{owner}/{repo}/actions/runs"

        params = {"per_page": per_page}

        if branch:
            params["branch"] = branch
        if event:
            params["event"] = event
        if status:
            params["status"] = status

        response = await self.client.get(endpoint, params=params)
        return response.get("workflow_runs", [])

    async def get_workflow_run(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> Dict[str, Any]:
        """
        Get workflow run details

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            Workflow run data
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}"
        return await self.client.get(endpoint)

    async def get_workflow_run_status(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> Dict[str, Any]:
        """
        Get workflow run status and conclusion

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            Status information
        """
        run = await self.get_workflow_run(owner, repo, run_id)

        return {
            "id": run["id"],
            "status": run["status"],  # queued, in_progress, completed
            "conclusion": run.get("conclusion"),  # success, failure, cancelled, etc.
            "created_at": run["created_at"],
            "updated_at": run["updated_at"],
            "html_url": run["html_url"],
        }

    async def wait_for_workflow_completion(
        self,
        owner: str,
        repo: str,
        run_id: int,
        poll_interval: int = 10,
        timeout: int = 3600,
    ) -> Dict[str, Any]:
        """
        Wait for workflow run to complete

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID
            poll_interval: Seconds between status checks
            timeout: Maximum wait time in seconds

        Returns:
            Final workflow run data

        Raises:
            TimeoutError: If workflow doesn't complete within timeout
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            run = await self.get_workflow_run(owner, repo, run_id)

            if run["status"] == "completed":
                return run

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Workflow run {run_id} did not complete within {timeout} seconds"
                )

            await asyncio.sleep(poll_interval)

    async def cancel_workflow_run(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> Dict[str, Any]:
        """
        Cancel a workflow run

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            Empty dict on success
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/cancel"
        return await self.client.post(endpoint)

    async def rerun_workflow(
        self,
        owner: str,
        repo: str,
        run_id: int,
        enable_debug_logging: bool = False,
    ) -> Dict[str, Any]:
        """
        Rerun a workflow

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID
            enable_debug_logging: Enable debug logging

        Returns:
            Empty dict on success
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun"
        payload = {}

        if enable_debug_logging:
            payload["enable_debug_logging"] = True

        return await self.client.post(endpoint, json=payload)

    async def list_workflow_run_artifacts(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> List[Dict[str, Any]]:
        """
        List artifacts for a workflow run

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            List of artifacts
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
        response = await self.client.get(endpoint)
        return response.get("artifacts", [])

    async def download_artifact(
        self,
        owner: str,
        repo: str,
        artifact_id: int,
    ) -> bytes:
        """
        Download a workflow artifact

        Args:
            owner: Repository owner
            repo: Repository name
            artifact_id: Artifact ID

        Returns:
            Artifact content as bytes
        """
        endpoint = f"/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"

        import httpx

        url = f"{self.client.base_url}/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"
        headers = self.client._get_headers()

        async with httpx.AsyncClient(timeout=self.client.timeout) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.content

    async def get_workflow_run_logs(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> bytes:
        """
        Download workflow run logs

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            Logs as bytes (zip file)
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/logs"

        import httpx

        url = f"{self.client.base_url}/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        headers = self.client._get_headers()

        async with httpx.AsyncClient(timeout=self.client.timeout) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.content

    async def delete_workflow_run_logs(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> Dict[str, Any]:
        """
        Delete workflow run logs

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            Empty dict on success
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        return await self.client.delete(endpoint)

    async def list_workflow_run_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> List[Dict[str, Any]]:
        """
        List jobs for a workflow run

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            List of jobs
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
        response = await self.client.get(endpoint)
        return response.get("jobs", [])

    async def get_job(
        self,
        owner: str,
        repo: str,
        job_id: int,
    ) -> Dict[str, Any]:
        """
        Get job details

        Args:
            owner: Repository owner
            repo: Repository name
            job_id: Job ID

        Returns:
            Job data
        """
        endpoint = f"/repos/{owner}/{repo}/actions/jobs/{job_id}"
        return await self.client.get(endpoint)

    async def get_job_logs(
        self,
        owner: str,
        repo: str,
        job_id: int,
    ) -> str:
        """
        Download job logs

        Args:
            owner: Repository owner
            repo: Repository name
            job_id: Job ID

        Returns:
            Logs as text
        """
        endpoint = f"/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"

        import httpx

        url = f"{self.client.base_url}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
        headers = self.client._get_headers()

        async with httpx.AsyncClient(timeout=self.client.timeout) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.text

    async def trigger_and_wait(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None,
        poll_interval: int = 10,
        timeout: int = 3600,
    ) -> Dict[str, Any]:
        """
        Trigger workflow and wait for completion

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or filename
            ref: Git ref
            inputs: Workflow inputs
            poll_interval: Seconds between status checks
            timeout: Maximum wait time in seconds

        Returns:
            Completed workflow run data
        """
        # Trigger workflow
        await self.trigger_workflow(owner, repo, workflow_id, ref, inputs)

        # Wait a bit for the run to appear
        await asyncio.sleep(5)

        # Find the latest run
        runs = await self.list_workflow_runs(
            owner=owner,
            repo=repo,
            workflow_id=workflow_id,
            branch=ref,
            per_page=1,
        )

        if not runs:
            raise Exception("Workflow run not found after triggering")

        run_id = runs[0]["id"]

        # Wait for completion
        return await self.wait_for_workflow_completion(
            owner=owner,
            repo=repo,
            run_id=run_id,
            poll_interval=poll_interval,
            timeout=timeout,
        )
