"""
Temporal client for starting and managing workflows

This module provides a convenient interface for starting workflows,
querying their status, and managing their lifecycle.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

from temporalio.client import Client, WorkflowHandle

from workflows import (
    PlanPatchPRWorkflow,
    IncrementalPatchWorkflow,
    IncidentSwarmWorkflow,
    ContinuousMonitoringWorkflow,
    CodeMigrationWorkflow,
    QualityGateWorkflow,
    ContinuousQualityWorkflow,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Task queue configuration
TASK_QUEUE = "autonomous-coding-task-queue"


class WorkflowClient:
    """
    Client for interacting with Temporal workflows
    """

    def __init__(
        self,
        temporal_host: str = "localhost:7233",
        namespace: str = "default",
        task_queue: str = TASK_QUEUE,
    ):
        """
        Initialize workflow client

        Args:
            temporal_host: Temporal server host:port
            namespace: Temporal namespace
            task_queue: Task queue name
        """
        self.temporal_host = temporal_host
        self.namespace = namespace
        self.task_queue = task_queue
        self.client: Optional[Client] = None

    async def connect(self):
        """Connect to Temporal server"""
        logger.info(f"Connecting to Temporal at {self.temporal_host}")
        self.client = await Client.connect(
            self.temporal_host,
            namespace=self.namespace,
        )
        logger.info(f"Connected to namespace: {self.namespace}")

    async def disconnect(self):
        """Disconnect from Temporal server"""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Temporal")

    async def start_plan_patch_pr(
        self,
        requirement: str,
        auto_merge: bool = False,
        workflow_id: Optional[str] = None,
    ) -> WorkflowHandle:
        """
        Start a Plan-Patch-PR workflow

        Args:
            requirement: User requirement/feature request
            auto_merge: Whether to auto-merge if all checks pass
            workflow_id: Optional workflow ID

        Returns:
            Workflow handle
        """
        if not self.client:
            await self.connect()

        workflow_id = workflow_id or f"plan-patch-pr-{asyncio.get_event_loop().time()}"

        logger.info(f"Starting Plan-Patch-PR workflow: {workflow_id}")

        handle = await self.client.start_workflow(
            PlanPatchPRWorkflow.run,
            args=[requirement, auto_merge],
            id=workflow_id,
            task_queue=self.task_queue,
            execution_timeout=timedelta(hours=2),
        )

        logger.info(f"Workflow started: {handle.id}")
        return handle

    async def start_incremental_patch(
        self,
        description: str,
        files_to_modify: list,
        workflow_id: Optional[str] = None,
    ) -> WorkflowHandle:
        """
        Start an incremental patch workflow

        Args:
            description: Patch description
            files_to_modify: Files to modify
            workflow_id: Optional workflow ID

        Returns:
            Workflow handle
        """
        if not self.client:
            await self.connect()

        workflow_id = workflow_id or f"patch-{asyncio.get_event_loop().time()}"

        logger.info(f"Starting incremental patch workflow: {workflow_id}")

        handle = await self.client.start_workflow(
            IncrementalPatchWorkflow.run,
            args=[description, files_to_modify],
            id=workflow_id,
            task_queue=self.task_queue,
            execution_timeout=timedelta(minutes=30),
        )

        logger.info(f"Workflow started: {handle.id}")
        return handle

    async def start_incident_response(
        self,
        alert: Dict[str, Any],
        num_diagnostic_agents: int = 3,
        auto_fix: bool = True,
        workflow_id: Optional[str] = None,
    ) -> WorkflowHandle:
        """
        Start an incident response workflow

        Args:
            alert: Alert information
            num_diagnostic_agents: Number of diagnostic agents
            auto_fix: Whether to automatically fix
            workflow_id: Optional workflow ID

        Returns:
            Workflow handle
        """
        if not self.client:
            await self.connect()

        workflow_id = workflow_id or f"incident-{alert.get('id', asyncio.get_event_loop().time())}"

        logger.info(f"Starting incident response workflow: {workflow_id}")

        handle = await self.client.start_workflow(
            IncidentSwarmWorkflow.run,
            args=[alert, num_diagnostic_agents, auto_fix],
            id=workflow_id,
            task_queue=self.task_queue,
            execution_timeout=timedelta(hours=1),
        )

        logger.info(f"Workflow started: {handle.id}")
        return handle

    async def start_code_migration(
        self,
        migration_type: str,
        source_version: str,
        target_version: str,
        incremental: bool = True,
        auto_rollback: bool = True,
        workflow_id: Optional[str] = None,
    ) -> WorkflowHandle:
        """
        Start a code migration workflow

        Args:
            migration_type: Type of migration
            source_version: Source version
            target_version: Target version
            incremental: Execute incrementally
            auto_rollback: Auto-rollback on failure
            workflow_id: Optional workflow ID

        Returns:
            Workflow handle
        """
        if not self.client:
            await self.connect()

        workflow_id = workflow_id or f"migration-{migration_type}-{asyncio.get_event_loop().time()}"

        logger.info(f"Starting code migration workflow: {workflow_id}")

        handle = await self.client.start_workflow(
            CodeMigrationWorkflow.run,
            args=[migration_type, source_version, target_version, incremental, auto_rollback],
            id=workflow_id,
            task_queue=self.task_queue,
            execution_timeout=timedelta(hours=4),
        )

        logger.info(f"Workflow started: {handle.id}")
        return handle

    async def start_quality_gate(
        self,
        pr_number: int,
        branch: str,
        attempt_auto_fix: bool = True,
        required_coverage: float = 80.0,
        required_score: float = 85.0,
        workflow_id: Optional[str] = None,
    ) -> WorkflowHandle:
        """
        Start a quality gate workflow

        Args:
            pr_number: PR number
            branch: Branch to check
            attempt_auto_fix: Attempt auto-fixes
            required_coverage: Required coverage %
            required_score: Required quality score
            workflow_id: Optional workflow ID

        Returns:
            Workflow handle
        """
        if not self.client:
            await self.connect()

        workflow_id = workflow_id or f"quality-gate-pr-{pr_number}"

        logger.info(f"Starting quality gate workflow: {workflow_id}")

        handle = await self.client.start_workflow(
            QualityGateWorkflow.run,
            args=[pr_number, branch, attempt_auto_fix, required_coverage, required_score],
            id=workflow_id,
            task_queue=self.task_queue,
            execution_timeout=timedelta(minutes=30),
        )

        logger.info(f"Workflow started: {handle.id}")
        return handle

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of a workflow

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow status
        """
        if not self.client:
            await self.connect()

        handle = self.client.get_workflow_handle(workflow_id)

        try:
            # Try to query the workflow status
            status = await handle.query("get_status")
            return status
        except Exception as e:
            logger.error(f"Failed to query workflow status: {e}")
            return {"error": str(e)}

    async def cancel_workflow(self, workflow_id: str):
        """
        Cancel a running workflow

        Args:
            workflow_id: Workflow ID
        """
        if not self.client:
            await self.connect()

        handle = self.client.get_workflow_handle(workflow_id)

        logger.info(f"Cancelling workflow: {workflow_id}")
        await handle.cancel()
        logger.info("Workflow cancelled")

    async def wait_for_result(self, workflow_id: str) -> Any:
        """
        Wait for workflow to complete and get result

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow result
        """
        if not self.client:
            await self.connect()

        handle = self.client.get_workflow_handle(workflow_id)

        logger.info(f"Waiting for workflow result: {workflow_id}")
        result = await handle.result()
        logger.info(f"Workflow completed: {workflow_id}")

        return result

    async def signal_workflow(
        self,
        workflow_id: str,
        signal_name: str,
        *args,
    ):
        """
        Send a signal to a running workflow

        Args:
            workflow_id: Workflow ID
            signal_name: Signal name
            args: Signal arguments
        """
        if not self.client:
            await self.connect()

        handle = self.client.get_workflow_handle(workflow_id)

        logger.info(f"Sending signal '{signal_name}' to workflow: {workflow_id}")
        await handle.signal(signal_name, *args)
        logger.info("Signal sent")


async def example_plan_patch_pr():
    """Example: Start a Plan-Patch-PR workflow"""
    client = WorkflowClient()

    try:
        # Start workflow
        handle = await client.start_plan_patch_pr(
            requirement="Add user authentication with OAuth2",
            auto_merge=False,
        )

        print(f"Workflow started: {handle.id}")
        print(f"Workflow URL: http://localhost:8233/namespaces/default/workflows/{handle.id}")

        # Wait for result
        result = await client.wait_for_result(handle.id)

        print("\nWorkflow completed!")
        print(f"PR URL: {result.pr_url}")
        print(f"Files changed: {len(result.files_changed)}")
        print(f"Quality score: {result.qa_score:.1f}")

    finally:
        await client.disconnect()


async def example_incident_response():
    """Example: Start an incident response workflow"""
    client = WorkflowClient()

    try:
        # Create alert
        alert = {
            'id': 'alert-123',
            'severity': 'critical',
            'service': 'api-service',
            'message': 'High error rate detected',
            'timestamp': '2024-01-01T12:00:00Z',
            'metrics': {},
            'logs': [],
        }

        # Start workflow
        handle = await client.start_incident_response(
            alert=alert,
            num_diagnostic_agents=3,
            auto_fix=True,
        )

        print(f"Incident response started: {handle.id}")

        # Wait for result
        result = await client.wait_for_result(handle.id)

        print("\nIncident response completed!")
        print(f"Root cause: {result.consensus.root_cause}")
        print(f"Confidence: {result.consensus.confidence:.2%}")
        print(f"Fix applied: {result.fix_applied}")
        if result.hotfix_pr_url:
            print(f"Hotfix PR: {result.hotfix_pr_url}")

    finally:
        await client.disconnect()


async def example_migration():
    """Example: Start a code migration workflow"""
    client = WorkflowClient()

    try:
        # Start workflow
        handle = await client.start_code_migration(
            migration_type="react-upgrade",
            source_version="16.14.0",
            target_version="18.2.0",
            incremental=True,
            auto_rollback=True,
        )

        print(f"Migration started: {handle.id}")

        # Poll for status
        while True:
            status = await client.get_workflow_status(handle.id)
            print(f"Progress: {status.get('completed_steps', 0)}/{status.get('total_steps', 0)} steps")
            await asyncio.sleep(5)

            if status.get('completed_steps') == status.get('total_steps'):
                break

        # Get result
        result = await client.wait_for_result(handle.id)

        print("\nMigration completed!")
        print(f"Completed steps: {result.completed_steps}/{result.total_steps}")
        print(f"PR URL: {result.final_pr_url}")

    finally:
        await client.disconnect()


def main():
    """Main entry point for examples"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python client.py <example>")
        print("Examples: plan_patch_pr, incident_response, migration")
        return

    example = sys.argv[1]

    if example == "plan_patch_pr":
        asyncio.run(example_plan_patch_pr())
    elif example == "incident_response":
        asyncio.run(example_incident_response())
    elif example == "migration":
        asyncio.run(example_migration())
    else:
        print(f"Unknown example: {example}")


if __name__ == "__main__":
    main()
