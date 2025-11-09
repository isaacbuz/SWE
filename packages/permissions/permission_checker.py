"""
Permission Checker for Tool Execution
"""

import logging
from typing import Optional, List, Dict, Any
from .models import Role, Permission, UserPermission, ToolPermission, PermissionAction, PermissionEffect
from .roles import DEFAULT_ROLES


class PermissionResult:
    """Result of permission check"""
    
    def __init__(
        self,
        allowed: bool,
        reason: str = "",
        role: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None
    ):
        self.allowed = allowed
        self.reason = reason
        self.role = role
        self.conditions = conditions or {}
    
    def __bool__(self):
        return self.allowed
    
    def __repr__(self):
        status = "ALLOWED" if self.allowed else "DENIED"
        return f"PermissionResult({status}, reason='{self.reason}', role={self.role})"


class PermissionChecker:
    """
    Permission checker for tool execution
    
    Features:
    - Role-based access control (RBAC)
    - Per-user permission overrides
    - Per-tool permission configuration
    - Permission inheritance
    - Condition-based permissions
    """
    
    def __init__(
        self,
        roles: Optional[Dict[str, Role]] = None,
        user_permissions: Optional[Dict[str, List[UserPermission]]] = None,
        tool_permissions: Optional[Dict[str, ToolPermission]] = None
    ):
        """
        Initialize permission checker
        
        Args:
            roles: Custom roles dictionary (defaults to DEFAULT_ROLES)
            user_permissions: User-specific permission overrides
            tool_permissions: Tool-specific permission configurations
        """
        self.roles = roles or DEFAULT_ROLES.copy()
        self.user_permissions = user_permissions or {}
        self.tool_permissions = tool_permissions or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def check_permission(
        self,
        user_id: str,
        user_roles: List[str],
        tool_name: str,
        action: PermissionAction = PermissionAction.EXECUTE,
        context: Optional[Dict[str, Any]] = None
    ) -> PermissionResult:
        """
        Check if user has permission to execute a tool
        
        Args:
            user_id: User ID
            user_roles: List of role IDs for the user
            tool_name: Name of the tool to execute
            action: Action to perform (default: EXECUTE)
            context: Additional context (e.g., tool arguments)
            
        Returns:
            PermissionResult indicating if permission is granted
        """
        context = context or {}
        
        # 1. Check user-specific overrides first (highest priority)
        user_override = self._check_user_override(user_id, tool_name, action)
        if user_override is not None:
            return user_override
        
        # 2. Check tool-specific permissions
        tool_perm = self.tool_permissions.get(tool_name)
        if tool_perm:
            # Check if tool has role restrictions
            if tool_perm.allowed_roles:
                if not any(role in tool_perm.allowed_roles for role in user_roles):
                    return PermissionResult(
                        allowed=False,
                        reason=f"Tool {tool_name} is restricted to roles: {tool_perm.allowed_roles}",
                        role=None
                    )
            
            if tool_perm.denied_roles:
                if any(role in tool_perm.denied_roles for role in user_roles):
                    return PermissionResult(
                        allowed=False,
                        reason=f"Tool {tool_name} is denied for roles: {tool_perm.denied_roles}",
                        role=None
                    )
        
        # 3. Check role-based permissions
        for role_id in user_roles:
            role = self.roles.get(role_id)
            if not role:
                continue
            
            # Get all permissions including inherited
            all_permissions = self._get_all_permissions(role)
            
            # Check each permission
            for perm in all_permissions:
                if self._matches_resource(perm.resource, tool_name):
                    if perm.action == action or perm.action == PermissionAction.ADMIN:
                        # Check conditions
                        if self._check_conditions(perm.conditions, context):
                            if perm.effect == PermissionEffect.ALLOW:
                                return PermissionResult(
                                    allowed=True,
                                    reason=f"Allowed by role {role.name}",
                                    role=role_id,
                                    conditions=perm.conditions
                                )
                            else:
                                return PermissionResult(
                                    allowed=False,
                                    reason=f"Denied by role {role.name}",
                                    role=role_id
                                )
        
        # 4. Default: deny if no explicit permission
        return PermissionResult(
            allowed=False,
            reason=f"No permission found for tool {tool_name}",
            role=None
        )
    
    def _check_user_override(
        self,
        user_id: str,
        tool_name: str,
        action: PermissionAction
    ) -> Optional[PermissionResult]:
        """Check user-specific permission overrides"""
        user_perms = self.user_permissions.get(user_id, [])
        
        for perm in user_perms:
            if perm.tool_name == tool_name and perm.action == action:
                # Check expiration
                if perm.expires_at:
                    from datetime import datetime
                    expires = datetime.fromisoformat(perm.expires_at)
                    if datetime.utcnow() > expires:
                        continue
                
                return PermissionResult(
                    allowed=perm.effect == PermissionEffect.ALLOW,
                    reason=f"User-specific override ({perm.effect.value})",
                    role=None
                )
        
        return None
    
    def _get_all_permissions(self, role: Role) -> List[Permission]:
        """Get all permissions for a role including inherited"""
        permissions = list(role.permissions)
        
        # Add inherited permissions
        for parent_role_id in role.inherits_from:
            parent_role = self.roles.get(parent_role_id)
            if parent_role:
                permissions.extend(self._get_all_permissions(parent_role))
        
        return permissions
    
    def _matches_resource(self, pattern: str, resource: str) -> bool:
        """
        Check if resource matches pattern
        
        Supports wildcards:
        - "*" matches everything
        - "github.*" matches all github tools
        - "create*" matches all tools starting with "create"
        """
        if pattern == "*":
            return True
        
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return resource.startswith(prefix + ".")
        
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return resource.startswith(prefix)
        
        return pattern == resource
    
    def _check_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if conditions are met"""
        if not conditions:
            return True
        
        for key, value in conditions.items():
            context_value = context.get(key)
            
            # Numeric comparisons
            if isinstance(value, (int, float)):
                if isinstance(context_value, (int, float)):
                    if key.startswith("max_"):
                        if context_value > value:
                            return False
                    elif key.startswith("min_"):
                        if context_value < value:
                            return False
                    else:
                        if context_value != value:
                            return False
                else:
                    return False
            
            # String/boolean comparisons
            elif context_value != value:
                return False
        
        return True
    
    def add_role(self, role: Role):
        """Add a custom role"""
        self.roles[role.id] = role
    
    def add_user_permission(self, user_id: str, permission: UserPermission):
        """Add user-specific permission override"""
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = []
        self.user_permissions[user_id].append(permission)
    
    def add_tool_permission(self, tool_name: str, permission: ToolPermission):
        """Add tool-specific permission configuration"""
        self.tool_permissions[tool_name] = permission
    
    def get_user_permissions(self, user_id: str, tool_name: Optional[str] = None) -> List[UserPermission]:
        """Get user permissions"""
        perms = self.user_permissions.get(user_id, [])
        if tool_name:
            return [p for p in perms if p.tool_name == tool_name]
        return perms
    
    def remove_user_permission(self, user_id: str, tool_name: str, action: PermissionAction):
        """Remove user-specific permission"""
        if user_id in self.user_permissions:
            self.user_permissions[user_id] = [
                p for p in self.user_permissions[user_id]
                if not (p.tool_name == tool_name and p.action == action)
            ]

