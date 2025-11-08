"""
Example usage of the event broadcaster for integrating real-time updates.

This module demonstrates how to use the broadcaster throughout the application.
"""
from typing import Optional, Dict, Any
from uuid import UUID

from events.broadcaster import get_broadcaster


# Example 1: Broadcasting project updates from an API endpoint
async def update_project_example(
    project_id: UUID,
    project_name: str,
    repository_url: str,
    status: str,
    updated_by: UUID,
    changes: Dict[str, Any]
) -> bool:
    """
    Example: Broadcasting project updates when a project is modified.

    In your FastAPI router (routers/projects.py):

    @router.put("/{project_id}")
    async def update_project(project_id: UUID, updates: ProjectUpdate):
        # ... Update database ...

        # Broadcast update to all interested clients
        broadcaster = get_broadcaster()
        success = await broadcaster.broadcast_project_updated(
            project_id=project_id,
            project_name=updates.name,
            repository_url=updates.repo_url,
            status=updates.status,
            updated_by=current_user.id,
            changes={"status": "updated", "fields": list(updates.dict().keys())}
        )

        return {"success": success, "project": project}
    """
    broadcaster = get_broadcaster()
    return await broadcaster.broadcast_project_updated(
        project_id=project_id,
        project_name=project_name,
        repository_url=repository_url,
        status=status,
        updated_by=updated_by,
        changes=changes
    )


# Example 2: Broadcasting workflow progress from Temporal
async def temporal_workflow_update_example(
    workflow_id: UUID,
    status: str,
    progress: int,
    current_step: str,
    total_steps: int,
    project_id: Optional[UUID] = None
) -> bool:
    """
    Example: Broadcasting workflow progress during Temporal execution.

    In your Temporal workflow or activity:

    from events.broadcaster import get_broadcaster

    @activity.defn
    async def report_workflow_progress(
        workflow_id: UUID,
        step_number: int,
        step_name: str,
        total_steps: int
    ):
        broadcaster = get_broadcaster()

        # Report progress as activity executes
        await broadcaster.broadcast_workflow_progress(
            workflow_id=workflow_id,
            status="running",
            progress=int((step_number / total_steps) * 100),
            current_step=step_name,
            total_steps=total_steps,
            project_id=project_id,
            logs=["Step started", f"Processing {step_name}"]
        )

        # Do actual work...
        # ...

        # Report completion
        await broadcaster.broadcast_workflow_progress(
            workflow_id=workflow_id,
            status="running",
            progress=int(((step_number + 1) / total_steps) * 100),
            current_step=step_name,
            total_steps=total_steps,
            project_id=project_id,
            logs=["Step completed successfully"]
        )
    """
    broadcaster = get_broadcaster()
    return await broadcaster.broadcast_workflow_progress(
        workflow_id=workflow_id,
        status=status,
        progress=progress,
        current_step=current_step,
        total_steps=total_steps,
        project_id=project_id
    )


# Example 3: Broadcasting agent status changes
async def agent_status_update_example(
    agent_id: UUID,
    agent_name: str,
    status: str,
    availability: int = 0
) -> bool:
    """
    Example: Broadcasting agent availability changes.

    In your agent service or status monitor:

    from events.broadcaster import get_broadcaster

    async def on_agent_status_changed(agent_id: UUID, new_status: str):
        broadcaster = get_broadcaster()
        await broadcaster.broadcast_agent_status_changed(
            agent_id=agent_id,
            agent_name="GPT-4 Agent",
            status=new_status,
            availability=calculate_availability(agent_id)
        )
    """
    broadcaster = get_broadcaster()
    return await broadcaster.broadcast_agent_status_changed(
        agent_id=agent_id,
        agent_name=agent_name,
        status=status,
        availability=availability
    )


# Example 4: Broadcasting GitHub PR events
async def pr_created_webhook_example(
    pr_id: UUID,
    project_id: UUID,
    title: str,
    author: str,
    github_url: str
) -> bool:
    """
    Example: Broadcasting new PR from GitHub webhook.

    In your webhook handler (routers/webhooks.py):

    from events.broadcaster import get_broadcaster

    @router.post("/github/webhook")
    async def github_webhook(payload: dict):
        if payload["action"] == "opened" and "pull_request" in payload:
            pr = payload["pull_request"]
            project = get_project_by_github_url(pr["head"]["repo"]["url"])

            broadcaster = get_broadcaster()
            await broadcaster.broadcast_pr_created(
                pr_id=UUID(pr["id"]),
                project_id=project.id,
                title=pr["title"],
                description=pr["body"],
                author=pr["user"]["login"],
                branch=pr["head"]["ref"],
                github_url=pr["html_url"],
                status=pr["state"]
            )
    """
    broadcaster = get_broadcaster()
    return await broadcaster.broadcast_pr_created(
        pr_id=pr_id,
        project_id=project_id,
        title=title,
        description=None,
        author=author,
        branch="",
        github_url=github_url,
        status="open"
    )


# Example 5: Broadcasting AI suggestions
async def ai_suggestion_example(
    suggestion_id: UUID,
    target_type: str,
    target_id: UUID,
    title: str,
    description: str,
    project_id: Optional[UUID] = None
) -> bool:
    """
    Example: Broadcasting AI suggestions from the AI Dock.

    In your AI service (services/ai_dock.py):

    from events.broadcaster import get_broadcaster

    async def generate_suggestions_for_pr(pr_id: UUID, project_id: UUID):
        broadcaster = get_broadcaster()

        # Generate suggestions...
        suggestions = await ai_model.analyze_pr(pr_id)

        for suggestion in suggestions:
            await broadcaster.broadcast_ai_suggestion(
                suggestion_id=UUID(suggestion["id"]),
                target_type="pr",
                target_id=pr_id,
                category=suggestion["category"],
                title=suggestion["title"],
                description=suggestion["description"],
                severity=suggestion["severity"],
                confidence=suggestion["confidence"],
                suggested_action=suggestion.get("action"),
                project_id=project_id
            )
    """
    broadcaster = get_broadcaster()
    return await broadcaster.broadcast_ai_suggestion(
        suggestion_id=suggestion_id,
        target_type=target_type,
        target_id=target_id,
        category="general",
        title=title,
        description=description,
        project_id=project_id
    )


# Example 6: Broadcasting issue updates
async def issue_updated_example(
    issue_id: UUID,
    project_id: UUID,
    title: str,
    status: str,
    assigned_to: Optional[UUID] = None
) -> bool:
    """
    Example: Broadcasting issue updates.

    In your issues router (routers/issues.py):

    @router.put("/{issue_id}")
    async def update_issue(issue_id: UUID, updates: IssueUpdate):
        # ... Update database ...

        broadcaster = get_broadcaster()
        await broadcaster.broadcast_issue_updated(
            issue_id=issue_id,
            project_id=project_id,
            title=updates.title,
            description=updates.description,
            status=updates.status,
            priority=updates.priority,
            assigned_to=updates.assigned_to
        )

        return {"success": True, "issue": issue}
    """
    broadcaster = get_broadcaster()
    return await broadcaster.broadcast_issue_updated(
        issue_id=issue_id,
        project_id=project_id,
        title=title,
        description=None,
        status=status,
        priority=None,
        assigned_to=assigned_to
    )
