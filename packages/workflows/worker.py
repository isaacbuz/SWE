"""
Temporal worker that executes workflows and activities

The worker connects to the Temporal server and polls for work,
executing workflows and activities as they are scheduled.
"""

import asyncio
import logging
from typing import Optional

from temporalio.client import Client
from temporalio.worker import Worker

# Import all workflows
from workflows import (
    PlanPatchPRWorkflow,
    IncrementalPatchWorkflow,
    IncidentSwarmWorkflow,
    ContinuousMonitoringWorkflow,
    CodeMigrationWorkflow,
    QualityGateWorkflow,
    ContinuousQualityWorkflow,
)

# Import all activities
from activities import agent_activities, github_activities, tool_activities

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Task queue configuration
TASK_QUEUE = "autonomous-coding-task-queue"


async def create_worker(
    client: Client,
    task_queue: str = TASK_QUEUE,
) -> Worker:
    """
    Create and configure a Temporal worker

    Args:
        client: Temporal client
        task_queue: Task queue name

    Returns:
        Configured worker
    """
    # Collect all activity functions
    activities = []

    # Agent activities
    for attr_name in dir(agent_activities):
        attr = getattr(agent_activities, attr_name)
        if hasattr(attr, '__temporal_activity_definition'):
            activities.append(attr)

    # GitHub activities
    for attr_name in dir(github_activities):
        attr = getattr(github_activities, attr_name)
        if hasattr(attr, '__temporal_activity_definition'):
            activities.append(attr)

    # Tool activities
    for attr_name in dir(tool_activities):
        attr = getattr(tool_activities, attr_name)
        if hasattr(attr, '__temporal_activity_definition'):
            activities.append(attr)

    # Create worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            PlanPatchPRWorkflow,
            IncrementalPatchWorkflow,
            IncidentSwarmWorkflow,
            ContinuousMonitoringWorkflow,
            CodeMigrationWorkflow,
            QualityGateWorkflow,
            ContinuousQualityWorkflow,
        ],
        activities=activities,
        max_concurrent_activities=10,
        max_concurrent_workflow_tasks=10,
    )

    logger.info(f"Worker created for task queue: {task_queue}")
    logger.info(f"Registered {len(activities)} activities")
    logger.info("Registered 7 workflows")

    return worker


async def run_worker(
    temporal_host: str = "localhost:7233",
    namespace: str = "default",
    task_queue: str = TASK_QUEUE,
):
    """
    Connect to Temporal and run the worker

    Args:
        temporal_host: Temporal server host:port
        namespace: Temporal namespace
        task_queue: Task queue name
    """
    logger.info(f"Connecting to Temporal server at {temporal_host}")

    # Connect to Temporal
    client = await Client.connect(
        temporal_host,
        namespace=namespace,
    )

    logger.info(f"Connected to Temporal namespace: {namespace}")

    # Create worker
    worker = await create_worker(client, task_queue)

    # Run the worker
    logger.info("Starting worker...")
    logger.info(f"Listening on task queue: {task_queue}")
    logger.info("Worker is ready to process workflows and activities")
    logger.info("Press Ctrl+C to stop the worker")

    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        raise


async def run_multi_worker(
    temporal_host: str = "localhost:7233",
    namespace: str = "default",
    num_workers: int = 3,
):
    """
    Run multiple workers for better throughput

    Args:
        temporal_host: Temporal server host:port
        namespace: Temporal namespace
        num_workers: Number of workers to run
    """
    logger.info(f"Starting {num_workers} workers")

    # Connect to Temporal
    client = await Client.connect(
        temporal_host,
        namespace=namespace,
    )

    # Create multiple workers
    workers = []
    for i in range(num_workers):
        worker = await create_worker(client, TASK_QUEUE)
        workers.append(worker)
        logger.info(f"Worker {i+1}/{num_workers} created")

    # Run all workers concurrently
    logger.info("Starting all workers...")
    try:
        await asyncio.gather(*[worker.run() for worker in workers])
    except KeyboardInterrupt:
        logger.info("Workers stopped by user")
    except Exception as e:
        logger.error(f"Workers error: {e}", exc_info=True)
        raise


def main():
    """Main entry point for the worker"""
    import argparse

    parser = argparse.ArgumentParser(description="Temporal worker for autonomous coding")
    parser.add_argument(
        "--host",
        default="localhost:7233",
        help="Temporal server host:port (default: localhost:7233)",
    )
    parser.add_argument(
        "--namespace",
        default="default",
        help="Temporal namespace (default: default)",
    )
    parser.add_argument(
        "--task-queue",
        default=TASK_QUEUE,
        help=f"Task queue name (default: {TASK_QUEUE})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of workers to run (default: 1)",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Autonomous Coding System - Temporal Worker")
    logger.info("=" * 60)
    logger.info(f"Temporal Server: {args.host}")
    logger.info(f"Namespace: {args.namespace}")
    logger.info(f"Task Queue: {args.task_queue}")
    logger.info(f"Number of Workers: {args.workers}")
    logger.info("=" * 60)

    # Run worker(s)
    if args.workers == 1:
        asyncio.run(run_worker(args.host, args.namespace, args.task_queue))
    else:
        asyncio.run(run_multi_worker(args.host, args.namespace, args.workers))


if __name__ == "__main__":
    main()
