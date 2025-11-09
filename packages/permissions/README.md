# Tool Permission System

Role-based access control (RBAC) for tool execution with fine-grained permissions.

## Features

- ✅ Role-based access control (RBAC)
- ✅ Default role definitions (admin, developer, agent, readonly, manager)
- ✅ Per-user permission overrides
- ✅ Per-tool permission configuration
- ✅ Permission inheritance
- ✅ Condition-based permissions
- ✅ Wildcard pattern matching
- ✅ Integration with ToolExecutor

## Quick Start

```python
from permissions import PermissionChecker, PermissionAction, DEFAULT_ROLES

# Initialize checker
checker = PermissionChecker()

# Check permission
result = checker.check_permission(
    user_id="user-123",
    user_roles=["developer"],
    tool_name="createIssues",
    action=PermissionAction.EXECUTE
)

if result.allowed:
    print(f"Permission granted: {result.reason}")
    # Execute tool
else:
    print(f"Permission denied: {result.reason}")
```

## Default Roles

### Admin
- Full access to all tools
- Can execute any tool
- System administration privileges

### Developer
- Can execute GitHub and code tools
- Cannot execute deployment tools
- Suitable for development work

### Agent
- Limited to read-only tools
- Can create issues (with limits)
- Cannot merge PRs or deploy
- Suitable for AI agents

### Read-Only
- Can only execute read/list operations
- Cannot create, update, or delete
- Suitable for viewing/analytics

### Manager
- Can execute orchestration tools
- Inherits developer permissions
- Cannot deploy directly

## Usage Examples

### Check Permission

```python
result = checker.check_permission(
    user_id="user-123",
    user_roles=["developer"],
    tool_name="createIssues",
    action=PermissionAction.EXECUTE,
    context={"max_issues": 5}
)
```

### Add User Override

```python
from permissions import UserPermission, PermissionEffect
from datetime import datetime, timedelta

override = UserPermission(
    user_id="user-123",
    tool_name="deployProduction",
    action=PermissionAction.EXECUTE,
    effect=PermissionEffect.ALLOW,
    expires_at=(datetime.utcnow() + timedelta(days=1)).isoformat()
)

checker.add_user_permission("user-123", override)
```

### Configure Tool Permissions

```python
from permissions import ToolPermission

tool_perm = ToolPermission(
    tool_name="deployProduction",
    requires_auth=True,
    allowed_roles=["admin", "manager"],
    denied_roles=["agent", "readonly"],
    cost_limit=100.0
)

checker.add_tool_permission("deployProduction", tool_perm)
```

## Integration with ToolExecutor

```python
from openapi_tools import ToolExecutor
from permissions import PermissionChecker

checker = PermissionChecker()

def check_permission(tool_name: str, user_id: str, user_roles: List[str]):
    result = checker.check_permission(
        user_id=user_id,
        user_roles=user_roles,
        tool_name=tool_name
    )
    if not result.allowed:
        raise PermissionError(result.reason)
    return result

executor = ToolExecutor(
    enableAuditLog=True,
    permissionChecker=check_permission
)
```

## License

MIT

