import { Role, Operation, Permission, UserPermissions, PermissionCheckResult, PermissionCondition } from "./types";
import { getEffectivePermissions } from "./RoleDefinitions";

export class PermissionChecker {
  private userPermissions: Map<string, UserPermissions> = new Map();

  constructor() {}

  addUser(userPermissions: UserPermissions): void {
    this.userPermissions.set(userPermissions.userId, userPermissions);
  }

  async canExecute(
    userId: string,
    toolName: string,
    operation: Operation,
    args?: Record<string, unknown>
  ): Promise<PermissionCheckResult> {
    const userPerms = this.userPermissions.get(userId);
    
    if (!userPerms) {
      return { allowed: false, reason: "User not found" };
    }

    // Check explicit denials first
    if (userPerms.deniedPermissions?.some((denied) => this.matchesPattern(toolName, denied))) {
      return { allowed: false, reason: "Explicitly denied" };
    }

    // Collect all permissions from roles
    const allPermissions: Permission[] = [];
    for (const role of userPerms.roles) {
      allPermissions.push(...getEffectivePermissions(role));
    }

    // Add custom permissions
    if (userPerms.customPermissions) {
      allPermissions.push(...userPerms.customPermissions);
    }

    // Check if any permission matches
    for (const permission of allPermissions) {
      if (this.matchesPattern(toolName, permission.toolName)) {
        // Check if operation is allowed
        if (permission.operations.includes(operation) || permission.operations.includes(Operation.ADMIN)) {
          // Check conditions
          if (permission.conditions && args) {
            if (!this.evaluateConditions(permission.conditions, args)) {
              continue;
            }
          }
          return { allowed: true, matchedPermission: permission };
        }
      }
    }

    return { allowed: false, reason: "No matching permission found" };
  }

  private matchesPattern(toolName: string, pattern: string): boolean {
    if (pattern === "*") return true;
    if (pattern.endsWith("/*")) {
      const prefix = pattern.slice(0, -2);
      return toolName.startsWith(prefix);
    }
    return toolName === pattern;
  }

  private evaluateConditions(conditions: PermissionCondition[], args: Record<string, unknown>): boolean {
    return conditions.every((condition) => {
      const value = args[condition.field];
      switch (condition.operator) {
        case "equals":
          return value === condition.value;
        case "contains":
          return String(value).includes(String(condition.value));
        case "in":
          return Array.isArray(condition.value) && condition.value.includes(value);
        case "matches":
          return new RegExp(String(condition.value)).test(String(value));
        default:
          return false;
      }
    });
  }

  async getUserPermissions(userId: string): Promise<Permission[]> {
    const userPerms = this.userPermissions.get(userId);
    if (!userPerms) return [];

    const allPermissions: Permission[] = [];
    for (const role of userPerms.roles) {
      allPermissions.push(...getEffectivePermissions(role));
    }
    if (userPerms.customPermissions) {
      allPermissions.push(...userPerms.customPermissions);
    }
    return allPermissions;
  }

  async grantPermission(userId: string, permission: Permission): Promise<void> {
    const userPerms = this.userPermissions.get(userId);
    if (!userPerms) {
      throw new Error("User not found");
    }
    if (!userPerms.customPermissions) {
      userPerms.customPermissions = [];
    }
    userPerms.customPermissions.push(permission);
  }

  async revokePermission(userId: string, toolName: string): Promise<void> {
    const userPerms = this.userPermissions.get(userId);
    if (!userPerms) {
      throw new Error("User not found");
    }
    if (!userPerms.customPermissions) return;
    userPerms.customPermissions = userPerms.customPermissions.filter(
      (p) => p.toolName !== toolName
    );
  }
}
