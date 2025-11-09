import { Role, RoleDefinition, Operation, Permission } from "./types";

export const DEFAULT_ROLES: RoleDefinition[] = [
  {
    name: Role.ADMIN,
    description: "Full system access",
    permissions: [{ toolName: "*", operations: [Operation.READ, Operation.WRITE, Operation.EXECUTE, Operation.DELETE, Operation.ADMIN] }],
  },
  {
    name: Role.DEVELOPER,
    description: "Development access",
    permissions: [
      { toolName: "github/*", operations: [Operation.READ, Operation.EXECUTE] },
      { toolName: "code/*", operations: [Operation.EXECUTE] },
      { toolName: "cicd/runTests", operations: [Operation.EXECUTE] },
    ],
  },
  {
    name: Role.AGENT,
    description: "AI agent with safe operations",
    permissions: [
      { toolName: "github/createIssues", operations: [Operation.EXECUTE] },
      { toolName: "code/analyzeCode", operations: [Operation.EXECUTE] },
    ],
  },
  {
    name: Role.READONLY,
    description: "Read-only access",
    permissions: [{ toolName: "*", operations: [Operation.READ] }],
  },
];

export function getRoleDefinition(role: Role): RoleDefinition | undefined {
  return DEFAULT_ROLES.find((r) => r.name === role);
}

export function getEffectivePermissions(role: Role): Permission[] {
  const roleDef = getRoleDefinition(role);
  if (!roleDef) return [];
  let permissions = [...roleDef.permissions];
  if (roleDef.inherits) {
    for (const inheritedRole of roleDef.inherits) {
      permissions = permissions.concat(getEffectivePermissions(inheritedRole));
    }
  }
  return permissions;
}
