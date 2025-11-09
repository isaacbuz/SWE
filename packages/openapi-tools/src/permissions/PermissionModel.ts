/**
 * Tool Permission Model
 * 
 * Defines role-based access control for tool execution.
 */

export enum Role {
  ADMIN = "admin",
  DEVELOPER = "developer",
  AGENT = "agent",
  READONLY = "readonly",
}

export interface PermissionCondition {
  /** Field to check */
  field: string;
  
  /** Comparison operator */
  operator: "equals" | "contains" | "matches" | "in" | "not_in";
  
  /** Value to compare against */
  value: unknown;
}

export interface Permission {
  /** Tool name (supports wildcards like "github/*" or "*") */
  toolName: string;
  
  /** Allowed operations */
  operations: string[]; // ["read", "write", "execute", "delete"]
  
  /** Optional conditions for fine-grained control */
  conditions?: PermissionCondition[];
}

export interface RoleDefinition {
  /** Role name */
  name: Role;
  
  /** Permissions for this role */
  permissions: Permission[];
  
  /** Roles to inherit permissions from */
  inherits?: Role[];
}

export interface UserPermissions {
  /** User ID */
  userId: string;
  
  /** User roles */
  roles: Role[];
  
  /** Custom permissions (overrides role permissions) */
  customPermissions?: Permission[];
  
  /** Denied permissions (explicitly denied) */
  deniedPermissions?: string[]; // Tool names
}

export class PermissionDeniedError extends Error {
  constructor(
    message: string,
    public userId: string,
    public toolName: string,
    public operation: string
  ) {
    super(message);
    this.name = "PermissionDeniedError";
  }
}

