# @ai-company/permissions

Role-Based Access Control (RBAC) system for tool execution in the AI Dev Team platform.

## Features

- **Role-Based Access Control**: Define permissions based on user roles
- **4 Default Roles**: Admin, Developer, Agent, ReadOnly
- **Flexible Permissions**: Wildcard matching, conditional permissions
- **Per-User Overrides**: Grant or deny specific permissions
- **Integration-Ready**: Designed to integrate with ToolExecutor

## Installation

```bash
npm install @ai-company/permissions
```

## Usage

```typescript
import { PermissionChecker, Role, Operation, UserPermissions } from '@ai-company/permissions';

// Create permission checker
const checker = new PermissionChecker();

// Add user with roles
checker.addUser({
  userId: 'user123',
  roles: [Role.DEVELOPER],
  customPermissions: [
    {
      toolName: 'custom/myTool',
      operations: [Operation.EXECUTE]
    }
  ]
});

// Check permission
const result = await checker.canExecute(
  'user123',
  'github/createIssues',
  Operation.EXECUTE
);

if (result.allowed) {
  // Execute tool
} else {
  console.error(result.reason);
}
```

## Default Roles

- **Admin**: Full access to all tools and operations
- **Developer**: Access to GitHub, code, and CI/CD tools
- **Agent**: Limited to safe operations (read, create draft PRs)
- **ReadOnly**: Read-only access to all tools

## API

### PermissionChecker

- `addUser(userPermissions: UserPermissions)`: Add user with roles
- `canExecute(userId, toolName, operation, args?)`: Check if user can execute tool
- `getUserPermissions(userId)`: Get all permissions for user
- `grantPermission(userId, permission)`: Grant custom permission
- `revokePermission(userId, toolName)`: Revoke permission

## License

MIT
