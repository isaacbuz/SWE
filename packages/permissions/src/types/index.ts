/**
 * Permission system types
 */

/**
 * User role
 */
export enum Role {
  ADMIN = 'admin',
  DEVELOPER = 'developer',
  VIEWER = 'viewer',
  GUEST = 'guest',
}

/**
 * Permission
 */
export interface Permission {
  /**
   * Tool name (or '*' for all tools)
   */
  tool: string;

  /**
   * Action (execute, read, write, etc.)
   */
  action: string;

  /**
   * Condition function (optional)
   */
  condition?: (context: PermissionContext) => boolean;
}

/**
 * Permission context
 */
export interface PermissionContext {
  userId: string;
  toolName: string;
  arguments: unknown;
  metadata?: Record<string, unknown>;
}

/**
 * Role definition
 */
export interface RoleDefinition {
  name: Role;
  permissions: Permission[];
  inherits?: Role[];
}

