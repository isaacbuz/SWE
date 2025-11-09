import { Role, Permission, PermissionContext, RoleDefinition } from './types';

/**
 * Default role definitions
 */
const DEFAULT_ROLES: RoleDefinition[] = [
  {
    name: Role.ADMIN,
    permissions: [
      { tool: '*', action: '*' }, // All tools, all actions
    ],
  },
  {
    name: Role.DEVELOPER,
    permissions: [
      { tool: '*', action: 'execute' },
      { tool: 'createIssues', action: '*' },
      { tool: 'createPR', action: '*' },
      { tool: 'updateIssue', action: '*' },
      { tool: 'commentOnIssue', action: '*' },
      { tool: 'analyzeCode', action: 'execute' },
      { tool: 'generateTests', action: 'execute' },
      { tool: 'refactorCode', action: 'execute' },
    ],
  },
  {
    name: Role.VIEWER,
    permissions: [
      { tool: '*', action: 'read' },
      { tool: 'analyzeCode', action: 'execute' },
    ],
  },
  {
    name: Role.GUEST,
    permissions: [
      { tool: 'analyzeCode', action: 'execute' },
    ],
  },
];

/**
 * Permission Checker
 * 
 * Implements RBAC for tool execution with role-based permissions
 * and conditional access control.
 */
export class PermissionChecker {
  private roles: Map<Role, RoleDefinition> = new Map();
  private userRoles: Map<string, Role[]> = new Map();

  constructor(customRoles?: RoleDefinition[]) {
    // Load default roles
    for (const role of DEFAULT_ROLES) {
      this.roles.set(role.name, role);
    }

    // Add custom roles
    if (customRoles) {
      for (const role of customRoles) {
        this.roles.set(role.name, role);
      }
    }
  }

  /**
   * Assign role to user
   */
  assignRole(userId: string, role: Role): void {
    const currentRoles = this.userRoles.get(userId) || [];
    if (!currentRoles.includes(role)) {
      this.userRoles.set(userId, [...currentRoles, role]);
    }
  }

  /**
   * Remove role from user
   */
  removeRole(userId: string, role: Role): void {
    const currentRoles = this.userRoles.get(userId) || [];
    this.userRoles.set(
      userId,
      currentRoles.filter((r) => r !== role)
    );
  }

  /**
   * Get user roles
   */
  getUserRoles(userId: string): Role[] {
    return this.userRoles.get(userId) || [Role.GUEST];
  }

  /**
   * Check if user has permission
   */
  hasPermission(
    userId: string,
    toolName: string,
    action: string,
    context?: Omit<PermissionContext, 'userId' | 'toolName'>
  ): boolean {
    const userRoles = this.getUserRoles(userId);

    // Check each role
    for (const roleName of userRoles) {
      const role = this.roles.get(roleName);
      if (!role) continue;

      // Check direct permissions
      if (this.checkRolePermissions(role, toolName, action, userId, context)) {
        return true;
      }

      // Check inherited roles
      if (role.inherits) {
        for (const inheritedRoleName of role.inherits) {
          const inheritedRole = this.roles.get(inheritedRoleName);
          if (
            inheritedRole &&
            this.checkRolePermissions(
              inheritedRole,
              toolName,
              action,
              userId,
              context
            )
          ) {
            return true;
          }
        }
      }
    }

    return false;
  }

  /**
   * Check role permissions
   */
  private checkRolePermissions(
    role: RoleDefinition,
    toolName: string,
    action: string,
    userId: string,
    context?: Omit<PermissionContext, 'userId' | 'toolName'>
  ): boolean {
    for (const permission of role.permissions) {
      // Check tool match
      const toolMatch =
        permission.tool === '*' || permission.tool === toolName;

      if (!toolMatch) continue;

      // Check action match
      const actionMatch =
        permission.action === '*' || permission.action === action;

      if (!actionMatch) continue;

      // Check condition if present
      if (permission.condition) {
        const permissionContext: PermissionContext = {
          userId,
          toolName,
          arguments: context?.arguments || {},
          metadata: context?.metadata,
        };

        if (!permission.condition(permissionContext)) {
          continue;
        }
      }

      return true;
    }

    return false;
  }

  /**
   * Get all permissions for a user
   */
  getUserPermissions(userId: string): Permission[] {
    const userRoles = this.getUserRoles(userId);
    const permissions: Permission[] = [];

    for (const roleName of userRoles) {
      const role = this.roles.get(roleName);
      if (role) {
        permissions.push(...role.permissions);
      }
    }

    return permissions;
  }
}

