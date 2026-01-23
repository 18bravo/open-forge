"""
Authentication and Authorization Module

This module provides centralized authentication and authorization for Open Forge:

- **provider**: OAuth2/OIDC provider abstraction for multiple identity providers
- **rbac**: Role-based access control with hierarchical roles
- **permissions**: Fine-grained permission definitions
- **row_level**: Row-level security policies for data access
- **session**: Session management with token refresh
- **middleware**: FastAPI middleware for request authentication
"""

from forge_core.auth.jwt_provider import JWTAuthProvider, JWTConfig
from forge_core.auth.middleware import (
    AuthMiddleware,
    AuthenticationError,
    AuthorizationError,
    configure_auth,
    get_auth_provider,
    get_current_user,
    get_current_user_optional,
    require_permission,
    require_role,
)
from forge_core.auth.permissions import Permission, PermissionSet
from forge_core.auth.provider import AuthProvider, AuthProviderConfig, AuthProviderType
from forge_core.auth.rbac import Role, RoleAssignment
from forge_core.auth.row_level import Filter, RowLevelPolicy
from forge_core.auth.session import Session, SessionManager
from forge_core.auth.user import User

__all__ = [
    # Provider
    "AuthProvider",
    "AuthProviderConfig",
    "AuthProviderType",
    # JWT Provider
    "JWTAuthProvider",
    "JWTConfig",
    # User
    "User",
    # RBAC
    "Role",
    "RoleAssignment",
    # Permissions
    "Permission",
    "PermissionSet",
    # Row-level security
    "RowLevelPolicy",
    "Filter",
    # Session
    "Session",
    "SessionManager",
    # Middleware
    "AuthMiddleware",
    "AuthenticationError",
    "AuthorizationError",
    "configure_auth",
    "get_auth_provider",
    "get_current_user",
    "get_current_user_optional",
    "require_permission",
    "require_role",
]
