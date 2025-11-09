"""
Permission System Data Models
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class PermissionAction(str, Enum):
    """Permission actions"""
    EXECUTE = "execute"
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class PermissionEffect(str, Enum):
    """Permission effect"""
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class Permission:
    """Single permission definition"""
    action: PermissionAction
    resource: str  # Tool name or pattern (e.g., "github.*", "createIssues")
    effect: PermissionEffect = PermissionEffect.ALLOW
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Role:
    """Role definition with permissions"""
    id: str
    name: str
    description: str
    permissions: List[Permission] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)  # Role IDs to inherit from


@dataclass
class UserPermission:
    """User-specific permission override"""
    user_id: str
    tool_name: str
    action: PermissionAction
    effect: PermissionEffect
    expires_at: Optional[str] = None  # ISO datetime string


@dataclass
class ToolPermission:
    """Tool-specific permission configuration"""
    tool_name: str
    default_role: Optional[str] = None  # Default role required
    requires_auth: bool = True
    rate_limit: Optional[int] = None
    cost_limit: Optional[float] = None
    allowed_roles: List[str] = field(default_factory=list)
    denied_roles: List[str] = field(default_factory=list)

