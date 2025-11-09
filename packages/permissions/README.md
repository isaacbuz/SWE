# @ai-company/permissions

RBAC permission system for tool execution.

## Overview

Role-based access control (RBAC) system for controlling tool execution permissions.

## Features

- ✅ Role-based permissions
- ✅ Conditional access control
- ✅ Role inheritance
- ✅ Default roles (Admin, Developer, Viewer, Guest)
- ✅ Custom role definitions

## Installation

```bash
pnpm add @ai-company/permissions
```

## Usage

### Basic Usage

```typescript
import { PermissionChecker, Role } from '@ai-company/permissions';

const checker = new PermissionChecker();

// Assign role to user
checker.assignRole('user-123', Role.DEVELOPER);

// Check permission
const canExecute = checker.hasPermission(
  'user-123',
  'createIssue',
  'execute'
);

if (canExecute) {
  // Execute tool
}
```

### Custom Roles

```typescript
import { PermissionChecker, Role, RoleDefinition } from '@ai-company/permissions';

const customRoles: RoleDefinition[] = [
  {
    name: Role.DEVELOPER,
    permissions: [
      { tool: 'createIssue', action: 'execute' },
      { tool: 'createPR', action: 'execute' },
      {
        tool: 'mergePR',
        action: 'execute',
        condition: (context) => {
          // Only allow merging own PRs
          return context.metadata?.prAuthor === context.userId;
        },
      },
    ],
  },
];

const checker = new PermissionChecker(customRoles);
```

## Default Roles

- **Admin**: All tools, all actions
- **Developer**: Most tools, execute action
- **Viewer**: Read-only access, limited execute
- **Guest**: Very limited access

## Related Packages

- `@ai-company/tool-executor` - Tool execution engine
- `@ai-company/audit-logging` - Audit logging

## License

MIT

