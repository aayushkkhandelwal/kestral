from enum import Enum
from typing import Set, Union

class UserRole(str, Enum):
    ADMIN = "Admin"
    INVESTIGATOR = "Investigator"
    OFFICER = "Officer"
    ANALYST = "Analyst"

class Permission(str, Enum):
    # User Management
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"

    # Camera Management
    CAMERAS_READ = "cameras:read"
    CAMERAS_CREATE = "cameras:create"
    CAMERAS_UPDATE = "cameras:update"
    CAMERAS_DELETE = "cameras:delete"
    CAMERAS_VIEW_IP = "cameras:view_ip"

    # Video & Inference
    VIDEOS_UPLOAD = "videos:upload"
    VIDEOS_READ = "videos:read"
    VIDEOS_DELETE = "videos:delete"

    # Evidence & Inspection
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_EXPORT = "evidence:export"

    # Cases
    CASES_READ = "cases:read"
    CASES_CREATE = "cases:create"
    CASES_UPDATE = "cases:update"
    CASES_DELETE = "cases:delete"
    CASES_ASSIGN = "cases:assign"

    # Alerts
    ALERTS_READ = "alerts:read"
    ALERTS_CREATE = "alerts:create"
    ALERTS_ACKNOWLEDGE = "alerts:acknowledge"

    # Dashboard & Audit
    DASHBOARD_STATS = "dashboard:stats"
    AUDIT_READ = "audit:read"

ROLE_PERMISSIONS = {
    UserRole.ADMIN: {p for p in Permission},
    UserRole.INVESTIGATOR: {
        Permission.CAMERAS_READ,
        Permission.VIDEOS_UPLOAD,
        Permission.VIDEOS_READ,
        Permission.EVIDENCE_READ,
        Permission.EVIDENCE_EXPORT,
        Permission.CASES_READ,
        Permission.CASES_CREATE,
        Permission.CASES_UPDATE,
        Permission.CASES_ASSIGN,
        Permission.ALERTS_READ,
        Permission.ALERTS_ACKNOWLEDGE,
        Permission.DASHBOARD_STATS,
    },
    UserRole.OFFICER: {
        Permission.CAMERAS_READ,
        Permission.VIDEOS_READ,
        Permission.EVIDENCE_READ,
        Permission.CASES_READ,
        Permission.ALERTS_READ,
        Permission.ALERTS_ACKNOWLEDGE,
        Permission.DASHBOARD_STATS,
    },
    UserRole.ANALYST: {
        Permission.CAMERAS_READ,
        Permission.VIDEOS_READ,
        Permission.EVIDENCE_READ,
        Permission.EVIDENCE_EXPORT,
        Permission.CASES_READ,
        Permission.DASHBOARD_STATS,
    },
}

def has_permission(role: Union[UserRole, str], permission: Union[Permission, str]) -> bool:
    role_str = role.value if hasattr(role, "value") else str(role)
    if role_str.lower() in ("admin", "userrole.admin"):
        return True

    try:
        user_role = UserRole(role_str.capitalize())
    except Exception:
        user_role = UserRole.OFFICER

    perm_str = permission.value if hasattr(permission, "value") else str(permission)

    # Permission grouping aliases
    if perm_str in ("cameras:write", "cameras:create", "cameras:update"):
        check_perms = {Permission.CAMERAS_CREATE, Permission.CAMERAS_UPDATE}
    elif perm_str in ("cases:write", "cases:create", "cases:update"):
        check_perms = {Permission.CASES_CREATE, Permission.CASES_UPDATE}
    elif perm_str in ("alerts:write", "alerts:acknowledge"):
        check_perms = {Permission.ALERTS_ACKNOWLEDGE, Permission.ALERTS_CREATE}
    else:
        try:
            check_perms = {Permission(perm_str)}
        except Exception:
            check_perms = set()

    role_perms = ROLE_PERMISSIONS.get(user_role, set())
    return any(p in role_perms for p in check_perms)

def can_assign_role(acting_role: Union[UserRole, str], target_role: Union[UserRole, str]) -> bool:
    role_str = acting_role.value if hasattr(acting_role, "value") else str(acting_role)
    return role_str.lower() in ("admin", "userrole.admin")
