/**
 * Permission Checker
 *
 * Checks if users have permission to execute tools.
 */

import {
  Role,
  Permission,
  PermissionCondition,
  RoleDefinition,
  UserPermissions,
  PermissionDeniedError,
} from "./PermissionModel.js";

export class PermissionChecker {
  private roleDefinitions: Map<Role, RoleDefinition> = new Map();
  private userPermissions: Map<string, UserPermissions> = new Map();

  constructor() {
    this.loadDefaultRoles();
  }

  /**
   * Load default role definitions
   */
  private loadDefaultRoles(): void {
    const defaultRoles: RoleDefinition[] = [
      {
        name: Role.ADMIN,
        permissions: [
          { toolName: "*", operations: ["*"] }, // All tools, all operations
        ],
      },
      {
        name: Role.DEVELOPER,
        permissions: [
          { toolName: "github/*", operations: ["read", "write", "execute"] },
          { toolName: "code/*", operations: ["read", "write", "execute"] },
          { toolName: "cicd/runTests", operations: ["execute"] },
          { toolName: "cicd/deployPreview", operations: ["execute"] },
          // Cannot delete branches, deploy production
        ],
      },
      {
        name: Role.AGENT,
        permissions: [
          { toolName: "github/createIssues", operations: ["execute"] },
          { toolName: "github/createPR", operations: ["execute"] },
          { toolName: "github/listIssues", operations: ["read"] },
          { toolName: "code/analyzeCode", operations: ["execute"] },
          { toolName: "code/generateTests", operations: ["execute"] },
          { toolName: "cicd/runTests", operations: ["execute"] },
          // Limited to safe, read-focused operations
        ],
      },
      {
        name: Role.READONLY,
        permissions: [
          { toolName: "*", operations: ["read"] }, // All tools, read-only
        ],
      },
    ];

    for (const roleDef of defaultRoles) {
      this.roleDefinitions.set(roleDef.name, roleDef);
    }
  }

  /**
   * Register a role definition
   */
  registerRole(roleDefinition: RoleDefinition): void {
    this.roleDefinitions.set(roleDefinition.name, roleDefinition);
  }

  /**
   * Set user permissions
   */
  setUserPermissions(userId: string, permissions: UserPermissions): void {
    this.userPermissions.set(userId, permissions);
  }

  /**
   * Get user permissions
   */
  getUserPermissions(userId: string): UserPermissions | undefined {
    return this.userPermissions.get(userId);
  }

  /**
   * Check if user can execute a tool
   */
  async canExecute(
    userId: string,
    toolName: string,
    operation: string,
    args?: Record<string, unknown>,
  ): Promise<boolean> {
    const userPerms = this.getUserPermissions(userId);

    if (!userPerms) {
      // Default: no permissions
      return false;
    }

    // Check denied permissions first
    if (userPerms.deniedPermissions?.includes(toolName)) {
      return false;
    }

    // Collect all permissions from roles
    const allPermissions = this.collectPermissions(userPerms);

    // Check if any permission allows this operation
    for (const permission of allPermissions) {
      if (this.matchesPermission(permission, toolName, operation)) {
        // Check conditions if present
        if (permission.conditions && args) {
          if (this.evaluateConditions(permission.conditions, args)) {
            return true;
          }
        } else {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * Collect all permissions for a user (roles + custom)
   */
  private collectPermissions(userPerms: UserPermissions): Permission[] {
    const permissions: Permission[] = [];
    const processedRoles = new Set<Role>();

    // Collect from roles (with inheritance)
    const collectFromRole = (role: Role) => {
      if (processedRoles.has(role)) {
        return; // Avoid cycles
      }
      processedRoles.add(role);

      const roleDef = this.roleDefinitions.get(role);
      if (roleDef) {
        permissions.push(...roleDef.permissions);

        // Collect from inherited roles
        if (roleDef.inherits) {
          for (const inheritedRole of roleDef.inherits) {
            collectFromRole(inheritedRole);
          }
        }
      }
    };

    for (const role of userPerms.roles) {
      collectFromRole(role);
    }

    // Add custom permissions
    if (userPerms.customPermissions) {
      permissions.push(...userPerms.customPermissions);
    }

    return permissions;
  }

  /**
   * Check if permission matches tool and operation
   */
  private matchesPermission(
    permission: Permission,
    toolName: string,
    operation: string,
  ): boolean {
    // Check tool name match (supports wildcards)
    const toolMatch = this.matchesPattern(permission.toolName, toolName);
    if (!toolMatch) {
      return false;
    }

    // Check operation match
    if (permission.operations.includes("*")) {
      return true; // All operations allowed
    }

    return permission.operations.includes(operation);
  }

  /**
   * Check if pattern matches string (supports wildcards)
   */
  private matchesPattern(pattern: string, value: string): boolean {
    if (pattern === "*") {
      return true;
    }

    // Convert wildcard pattern to regex
    const regexPattern = pattern.replace(/\*/g, ".*").replace(/\?/g, ".");

    const regex = new RegExp(`^${regexPattern}$`);
    return regex.test(value);
  }

  /**
   * Evaluate permission conditions
   */
  private evaluateConditions(
    conditions: PermissionCondition[],
    args: Record<string, unknown>,
  ): boolean {
    for (const condition of conditions) {
      const fieldValue = args[condition.field];

      switch (condition.operator) {
        case "equals":
          if (fieldValue !== condition.value) {
            return false;
          }
          break;

        case "contains":
          if (
            typeof fieldValue === "string" &&
            typeof condition.value === "string"
          ) {
            if (!fieldValue.includes(condition.value)) {
              return false;
            }
          } else {
            return false;
          }
          break;

        case "matches":
          if (
            typeof fieldValue === "string" &&
            typeof condition.value === "string"
          ) {
            const regex = new RegExp(condition.value);
            if (!regex.test(fieldValue)) {
              return false;
            }
          } else {
            return false;
          }
          break;

        case "in":
          if (Array.isArray(condition.value)) {
            if (!condition.value.includes(fieldValue)) {
              return false;
            }
          } else {
            return false;
          }
          break;

        case "not_in":
          if (Array.isArray(condition.value)) {
            if (condition.value.includes(fieldValue)) {
              return false;
            }
          } else {
            return false;
          }
          break;

        default:
          return false;
      }
    }

    return true;
  }

  /**
   * Grant permission to user
   */
  async grantPermission(userId: string, permission: Permission): Promise<void> {
    const userPerms = this.getUserPermissions(userId) || {
      userId,
      roles: [],
      customPermissions: [],
    };

    if (!userPerms.customPermissions) {
      userPerms.customPermissions = [];
    }

    // Remove existing permission for same tool if exists
    userPerms.customPermissions = userPerms.customPermissions.filter(
      (p) => p.toolName !== permission.toolName,
    );

    userPerms.customPermissions.push(permission);
    this.setUserPermissions(userId, userPerms);
  }

  /**
   * Revoke permission from user
   */
  async revokePermission(userId: string, toolName: string): Promise<void> {
    const userPerms = this.getUserPermissions(userId);
    if (!userPerms) {
      return;
    }

    if (userPerms.customPermissions) {
      userPerms.customPermissions = userPerms.customPermissions.filter(
        (p) => p.toolName !== toolName,
      );
    }

    // Add to denied list
    if (!userPerms.deniedPermissions) {
      userPerms.deniedPermissions = [];
    }
    if (!userPerms.deniedPermissions.includes(toolName)) {
      userPerms.deniedPermissions.push(toolName);
    }

    this.setUserPermissions(userId, userPerms);
  }

  /**
   * Get all permissions for a user
   */
  async getUserPermissionsList(userId: string): Promise<Permission[]> {
    const userPerms = this.getUserPermissions(userId);
    if (!userPerms) {
      return [];
    }

    return this.collectPermissions(userPerms);
  }
}
