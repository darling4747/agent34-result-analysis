"""Authentication and user management routes."""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...models import User, UserAuditLog
from ...security.auth import get_current_active_user, get_current_user, require_role
from ...security.permissions import P
from ...security.tokens import decode_access_token, TokenError
from ...services.auth_service import AuthError, AuthService

router = APIRouter()


# ---- Request / Response schemas (inline for auth routes) ----

class LoginRequest(BaseModel):
    email: str
    password: str


class MfaVerifyLoginRequest(BaseModel):
    mfa_token: str
    totp_code: Optional[str] = None
    recovery_code: Optional[str] = None


class MfaVerifySetupRequest(BaseModel):
    totp_code: str
    recovery_codes: list[str]


class MfaDisableRequest(BaseModel):
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12)
    confirm_password: str


class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    faculty_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    must_change_password: bool
    mfa_enabled: bool = False
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None


# ---- Endpoints ----

@router.post("/login", tags=["Authentication"])
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user. Returns tokens + must_change_password flag."""
    settings = get_settings()
    svc = AuthService(db, settings)
    ip = request.client.host if request.client else ""
    try:
        result = svc.login(body.email, body.password, ip)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return {"success": True, "data": result}


@router.post("/change-initial-password", tags=["Authentication"])
def change_initial_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),  # allows must_change_password users
):
    """Force password reset — only valid when must_change_password is TRUE."""
    if not user.must_change_password:
        raise HTTPException(status_code=400, detail="Password change not required for this account.")
    settings = get_settings()
    svc = AuthService(db, settings)
    try:
        result = svc.change_initial_password(
            user,
            body.current_password,
            body.new_password,
            body.confirm_password,
        )
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "data": result}


@router.post("/logout", tags=["Authentication"])
def logout(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Revoke all refresh tokens for the current user."""
    from ...models import RefreshToken
    db.query(RefreshToken).filter_by(user_id=user.id).update({"revoked": True})
    db.commit()
    log = UserAuditLog(user_id=user.id, action="LOGOUT", success=True)
    db.add(log)
    db.commit()
    return {"success": True, "message": "Logged out."}


@router.get("/me", tags=["Authentication"])
def me(user: User = Depends(get_current_active_user)):
    """Return current user profile."""
    from ...security.permissions import ROLE_PERMISSIONS
    return {
        "success": True,
        "data": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.name if user.role else None,
            "department": user.department,
            "is_active": user.is_active,
            "mfa_enabled": user.mfa_enabled,
            "permissions": ROLE_PERMISSIONS.get(user.role.name, []) if user.role else [],
        },
    }


# ---- Admin user management ----

@router.post("/admin/users", tags=["User Management"])
def create_user(
    body: CreateUserRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("PLATFORM_ADMIN")),
):
    """PLATFORM_ADMIN only: create a new user account."""
    settings = get_settings()
    svc = AuthService(db, settings)
    try:
        result = svc.create_user(
            admin=admin,
            email=body.email,
            full_name=body.full_name,
            role_name=body.role,
            department=body.department,
            faculty_id=body.faculty_id,
        )
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "data": result}


@router.get("/admin/users", tags=["User Management"])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("PLATFORM_ADMIN")),
):
    """PLATFORM_ADMIN only: list all users (no passwords returned)."""
    settings = get_settings()
    svc = AuthService(db, settings)
    return {"success": True, "data": svc.list_users()}


@router.patch("/admin/users/{user_id}/deactivate", tags=["User Management"])
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("PLATFORM_ADMIN")),
):
    settings = get_settings()
    svc = AuthService(db, settings)
    try:
        svc.deactivate_user(admin, user_id)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "message": f"User {user_id} deactivated."}


@router.patch("/admin/users/{user_id}/activate", tags=["User Management"])
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("PLATFORM_ADMIN")),
):
    settings = get_settings()
    svc = AuthService(db, settings)
    try:
        svc.activate_user(admin, user_id)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "message": f"User {user_id} activated."}


@router.post("/admin/users/{user_id}/force-reset", tags=["User Management"])
def force_reset(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("PLATFORM_ADMIN")),
):
    """Generate new temporary password for a user. Returns temp password ONCE."""
    settings = get_settings()
    svc = AuthService(db, settings)
    try:
        result = svc.force_password_reset(admin, user_id)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "data": result}


@router.get("/audit-logs", tags=["User Management"])
def audit_logs(
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("PLATFORM_ADMIN", "AUDITOR")),
):
    """Return recent security audit log entries (last 200)."""
    logs = (
        db.query(UserAuditLog)
        .order_by(UserAuditLog.created_at.desc())
        .limit(200)
        .all()
    )
    return {
        "success": True,
        "data": [
            {
                "id": l.id,
                "user_id": l.user_id,
                "action": l.action,
                "ip_address": l.ip_address,
                "details": l.details,
                "success": l.success,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }


# ---- Multi-Factor Authentication (MFA) endpoints ----

@router.post("/mfa/verify", tags=["Authentication"])
def verify_mfa_login(body: MfaVerifyLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Complete 2-step login with temporary mfa_token + 6-digit TOTP code or recovery code."""
    try:
        payload = decode_access_token(body.mfa_token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid MFA challenge token.")
    except TokenError:
        raise HTTPException(status_code=401, detail="MFA challenge token has expired or is invalid.")

    settings = get_settings()
    svc = AuthService(db, settings)
    ip = request.client.host if request.client else ""
    try:
        result = svc.verify_mfa_login(
            user_id=user_id,
            totp_code=body.totp_code,
            recovery_code=body.recovery_code,
            ip=ip,
        )
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return {"success": True, "data": result}


@router.get("/mfa/status", tags=["Authentication"])
def mfa_status(user: User = Depends(get_current_active_user)):
    """Get current user's MFA configuration status."""
    return {
        "success": True,
        "data": {
            "mfa_enabled": user.mfa_enabled,
            "mfa_enabled_at": user.mfa_enabled_at.isoformat() if user.mfa_enabled_at else None,
        },
    }


@router.post("/mfa/setup", tags=["Authentication"])
def mfa_setup(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Initiate MFA setup: returns secret key, QR code data URI, and recovery codes."""
    settings = get_settings()
    svc = AuthService(db, settings)
    result = svc.setup_mfa(user)
    return {"success": True, "data": result}


@router.post("/mfa/verify-setup", tags=["Authentication"])
def mfa_verify_setup(
    body: MfaVerifySetupRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Verify 6-digit TOTP code to activate MFA for user account."""
    settings = get_settings()
    svc = AuthService(db, settings)
    try:
        result = svc.verify_mfa_setup(user, body.totp_code, body.recovery_codes)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "data": result}


@router.post("/mfa/disable", tags=["Authentication"])
def mfa_disable(
    body: MfaDisableRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Disable MFA after verifying current password."""
    settings = get_settings()
    svc = AuthService(db, settings)
    try:
        result = svc.disable_mfa(user, body.password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "data": result}


@router.post("/mfa/regenerate-recovery-codes", tags=["Authentication"])
def mfa_regenerate_recovery_codes(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Regenerate new MFA recovery codes for account."""
    settings = get_settings()
    svc = AuthService(db, settings)
    try:
        result = svc.regenerate_mfa_recovery_codes(user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "data": result}


@router.post("/admin/users/{user_id}/mfa/reset", tags=["User Management"])
def admin_reset_mfa(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("PLATFORM_ADMIN")),
):
    """PLATFORM_ADMIN only: reset MFA state for a user who lost their device."""
    settings = get_settings()
    svc = AuthService(db, settings)
    try:
        result = svc.reset_user_mfa(admin, user_id)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "data": result}