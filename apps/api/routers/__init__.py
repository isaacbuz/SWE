"""
API routers module.
"""
from routers.projects import router as projects_router
from routers.agents import router as agents_router
from routers.issues import router as issues_router
from routers.prs import router as prs_router
from routers.analytics import router as analytics_router
from routers.skills import router as skills_router

__all__ = [
    "projects_router",
    "agents_router",
    "issues_router",
    "prs_router",
    "analytics_router",
    "skills_router",
]
