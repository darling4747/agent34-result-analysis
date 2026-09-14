"""FastAPI authentication and RBAC dependencies."""
from __future__ import annotations
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from .tokens import TokenError, decode_access_token

_bearer = HTTPBearer(auto_error=False)


def _get_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return credentials.credentials


def get_current_user(
    token: str = Depends(_get_token),
    db: Session = Depends(get_db),
) -> User:
    """Decode JWT and return User. Raises 401 if invalid."""
    try:
        payload = decode_access_token(token)
    except TokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found or inactive.")
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Ensure account is active and password change not required for general endpoints."""
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PASSWORD_CHANGE_REQUIRED",
        )
    return user


def require_permission(*permissions: str):
    """Factory: returns a FastAPI dependency that enforces the given permission(s)."""
    def _dep(user: User = Depends(get_current_active_user)) -> User:
        user_perms = set(_role_permissions(user.role.name))
        for perm in permissions:
            if perm not in user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {perm} required.",
                )
        return user
    return _dep


def require_role(*roles: str):
    """Factory: returns dependency that enforces role membership."""
    def _dep(user: User = Depends(get_current_active_user)) -> User:
        if user.role.name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {roles}.",
            )
        return user
    return _dep


def _role_permissions(role_name: str) -> list[str]:
    from .permissions import ROLE_PERMISSIONS
    return ROLE_PERMISSIONS.get(role_name, [])


def enforce_department_scope(user: User, requested_department: Optional[str]) -> Optional[str]:
    """
    HOD / FACULTY may only access their own department.
    Returns the effective department to use in queries.
    Raises 403 if HOD requests a different department.
    """
    role = user.role.name
    if role in ("PLATFORM_ADMIN", "DEAN", "IQAC", "MANAGEMENT", "AUDITOR"):
        return requested_department
    if role in ("HOD", "FACULTY"):
        user_dept = user.department or "Computer Science & Engineering"
        if requested_department:
            req_clean = requested_department.strip().lower()
            user_clean = user_dept.strip().lower()
            dept_aliases = {
                "cse": "computer science & engineering",
                "ece": "electronics & communication engineering",
                "mech": "mechanical engineering",
                "civil": "civil engineering",
                "eee": "electrical & electronics engineering",
                "it": "information technology",
            }
            norm_req = dept_aliases.get(req_clean, req_clean)
            norm_user = dept_aliases.get(user_clean, user_clean)
            if norm_req != norm_user:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access restricted to your department.")
        return user.department or requested_department
    return requested_department
