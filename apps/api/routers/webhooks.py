"""
GitHub webhook endpoints for receiving GitHub events.
"""
from typing import Dict, Any

from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse

from packages.integrations.github.webhooks import WebhookHandler
from middleware import limiter


router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Initialize webhook handler
webhook_handler = WebhookHandler(secret=None)  # TODO: Load from settings


@router.post(
    "/github",
    status_code=status.HTTP_200_OK,
    summary="GitHub webhook endpoint"
)
@limiter.limit("100/minute")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: str = Header(None, alias="X-GitHub-Delivery")
) -> JSONResponse:
    """
    Handle GitHub webhook events.
    
    Supports:
    - Issues (opened, closed, assigned, etc.)
    - Pull requests (opened, closed, merged, etc.)
    - Push events
    - Workflow runs
    - And more
    
    - **X-GitHub-Event**: Event type (issues, pull_request, push, etc.)
    - **X-Hub-Signature-256**: Webhook signature for verification
    - **X-GitHub-Delivery**: Unique delivery ID
    """
    # Get raw payload
    payload = await request.body()
    
    # Handle webhook event
    try:
        results = await webhook_handler.handle_event(
            payload=payload,
            event_type=x_github_event,
            signature=x_hub_signature_256 or ""
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "event_type": x_github_event,
                "delivery_id": x_github_delivery,
                "handlers_executed": len(results)
            }
        )
    except Exception as e:
        # Log error but return 200 to GitHub (don't retry)
        # TODO: Proper error logging
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "error",
                "message": "Webhook processing failed",
                "event_type": x_github_event
            }
        )


@router.get(
    "/github/health",
    summary="GitHub webhook health check"
)
async def github_webhook_health() -> Dict[str, str]:
    """
    Health check endpoint for GitHub webhooks.
    
    Returns webhook handler status.
    """
    return {
        "status": "healthy",
        "handler": "WebhookHandler",
        "supported_events": [
            "issues",
            "pull_request",
            "push",
            "workflow_run",
            "check_run",
            "status"
        ]
    }

