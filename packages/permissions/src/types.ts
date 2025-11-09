export enum Role {
  ADMIN = "admin",
  DEVELOPER = "developer",
  AGENT = "agent",
  READONLY = "readonly",
}

export enum Operation {
  READ = "read",
  WRITE = "write",
  EXECUTE = "execute",
  DELETE = "delete",
  ADMIN = "admin",
}

export interface Permission {
  toolName: string;
  operations: Operation[];
  conditions?: PermissionCondition[];
}

export interface PermissionCondition {
  field: string;
  operator: "equals" | "contains" | "matches" | "in";
  value: unknown;
}

export interface RoleDefinition {
  name: Role;
  description: string;
  permissions: Permission[];
  inherits?: Role[];
}

export interface UserPermissions {
  userId: string;
  roles: Role[];
  customPermissions?: Permission[];
  deniedPermissions?: string[];
}

export interface PermissionCheckResult {
  allowed: boolean;
  reason?: string;
  matchedPermission?: Permission;
}
