"""
API routers module.
"""
from routers.auth import router as auth_router
from routers.projects import router as projects_router
from routers.agents import router as agents_router
from routers.issues import router as issues_router
from routers.prs import router as prs_router
from routers.analytics import router as analytics_router
from routers.skills import router as skills_router
from routers.webhooks import router as webhooks_router

__all__ = [
    "auth_router",
    "projects_router",
    "agents_router",
    "issues_router",
    "prs_router",
    "analytics_router",
    "skills_router",
    "webhooks_router",
]
