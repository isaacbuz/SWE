"""
Default Role Definitions
"""

from .models import Role, Permission, PermissionAction, PermissionEffect

# Default roles for the system
DEFAULT_ROLES = {
    "admin": Role(
        id="admin",
        name="Administrator",
        description="Full access to all tools and system functions",
        permissions=[
            Permission(
                action=PermissionAction.ADMIN,
                resource="*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="*",
                effect=PermissionEffect.ALLOW
            ),
        ]
    ),
    
    "developer": Role(
        id="developer",
        name="Developer",
        description="Can execute code and GitHub tools, but not deployment tools",
        permissions=[
            Permission(
                action=PermissionAction.EXECUTE,
                resource="github.*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="code.*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="analyzeCode",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="runTests",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="deploy.*",
                effect=PermissionEffect.DENY
            ),
        ]
    ),
    
    "agent": Role(
        id="agent",
        name="AI Agent",
        description="Limited to read-only tools and approved write operations",
        permissions=[
            Permission(
                action=PermissionAction.EXECUTE,
                resource="github.list*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="code.analyze*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="github.createIssues",
                effect=PermissionEffect.ALLOW,
                conditions={"max_issues": 10}
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="github.createPullRequest",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="github.merge*",
                effect=PermissionEffect.DENY
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="deploy.*",
                effect=PermissionEffect.DENY
            ),
        ]
    ),
    
    "readonly": Role(
        id="readonly",
        name="Read-Only",
        description="Can only execute read-only tools",
        permissions=[
            Permission(
                action=PermissionAction.EXECUTE,
                resource="*.list*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="*.get*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="*.create*",
                effect=PermissionEffect.DENY
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="*.update*",
                effect=PermissionEffect.DENY
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="*.delete*",
                effect=PermissionEffect.DENY
            ),
        ]
    ),
    
    "manager": Role(
        id="manager",
        name="Manager",
        description="Can execute high-level orchestration tools",
        permissions=[
            Permission(
                action=PermissionAction.EXECUTE,
                resource="github.*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="code.*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="cicd.*",
                effect=PermissionEffect.ALLOW
            ),
            Permission(
                action=PermissionAction.EXECUTE,
                resource="deploy.*",
                effect=PermissionEffect.DENY
            ),
        ],
        inherits_from=["developer"]
    ),
}

