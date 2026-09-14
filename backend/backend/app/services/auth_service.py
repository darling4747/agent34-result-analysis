"""Authentication and user management service."""
from __future__ import annotations
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..config import Settings
from ..models import RefreshToken, Role, RolePermission, Permission, User, UserAuditLog, MFARecoveryCode
from ..security.password import (
    generate_temp_password,
    hash_password,
    validate_password_policy,
    verify_password,
    PasswordPolicyError,
)
from ..security.permissions import ALL_PERMISSIONS, ROLE_PERMISSIONS, VALID_ROLES
from ..security.tokens import (
    create_access_token,
    create_refresh_token_value,
    hash_refresh_token,
)
from ..security.mfa import (
    decrypt_mfa_secret,
    encrypt_mfa_secret,
    generate_totp_secret,
    generate_provisioning_uri,
    generate_qr_code_data_uri,
    verify_totp_code,
    generate_recovery_codes,
    hash_recovery_code,
)


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    # ------------------------------------------------------------------
    # Bootstrap: seed roles and permissions (idempotent)
    # ------------------------------------------------------------------
    def seed_roles_and_permissions(self) -> None:
        for perm_name in ALL_PERMISSIONS:
            existing = self.db.query(Permission).filter_by(name=perm_name).first()
            if not existing:
                self.db.add(Permission(name=perm_name, description=perm_name))
        self.db.flush()

        for role_name, perms in ROLE_PERMISSIONS.items():
            role = self.db.query(Role).filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=role_name)
                self.db.add(role)
                self.db.flush()
            for perm_name in perms:
                perm = self.db.query(Permission).filter_by(name=perm_name).first()
                if perm:
                    exists = self.db.query(RolePermission).filter_by(
                        role_id=role.id, permission_id=perm.id
                    ).first()
                    if not exists:
                        self.db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        self.db.commit()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def login(self, email: str, password: str, ip: str = "") -> dict:
        user = self.db.query(User).filter_by(email=email.lower()).first()
        if not user:
            self._audit(None, "LOGIN_FAILED", ip, f"Unknown email: {email}", success=False)
            raise AuthError("Invalid email or password.")
        if not user.is_active:
            self._audit(user.id, "LOGIN_BLOCKED", ip, "Account inactive", success=False)
            raise AuthError("Account is inactive. Contact your administrator.")

        # Check temporary password expiry
        if user.must_change_password and user.temp_password_expires_at:
            if datetime.now(timezone.utc) > user.temp_password_expires_at.replace(tzinfo=timezone.utc):
                self._audit(user.id, "LOGIN_FAILED", ip, "Temp password expired", success=False)
                raise AuthError("Temporary password has expired. Contact your administrator to reset.")

        if not verify_password(password, user.password_hash):
            user.failed_login_count += 1
            self.db.commit()
            self._audit(user.id, "LOGIN_FAILED", ip, "Wrong password", success=False)
            raise AuthError("Invalid email or password.")

        # Successful password verification
        user.failed_login_count = 0
        self.db.commit()

        role_name = user.role.name
        permissions = ROLE_PERMISSIONS.get(role_name, [])

        # Check MFA requirement
        if user.mfa_enabled:
            # Issue temporary 5-minute MFA challenge token (no API permissions attached)
            mfa_token = create_access_token(user.id, user.email, role_name, [], expires_delta=timedelta(minutes=5))
            self._audit(user.id, "MFA_CHALLENGE_ISSUED", ip, "Awaiting TOTP code", success=True)
            return {
                "mfa_required": True,
                "mfa_token": mfa_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": role_name,
                    "department": user.department,
                },
            }

        # If MFA not enabled, issue full session tokens
        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()
        self._audit(user.id, "LOGIN_SUCCESS", ip, "", success=True)

        access_token = create_access_token(user.id, user.email, role_name, permissions)
        refresh_raw = create_refresh_token_value()
        self._store_refresh_token(user.id, refresh_raw)

        return {
            "mfa_required": False,
            "access_token": access_token,
            "refresh_token": refresh_raw,
            "token_type": "bearer",
            "must_change_password": user.must_change_password,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": role_name,
                "department": user.department,
                "permissions": permissions,
                "mfa_enabled": False,
            },
        }

    # ------------------------------------------------------------------
    # MFA verification and management
    # ------------------------------------------------------------------
    def verify_mfa_login(
        self,
        user_id: int,
        totp_code: Optional[str] = None,
        recovery_code: Optional[str] = None,
        ip: str = "",
    ) -> dict:
        user = self.db.get(User, user_id)
        if not user or not user.is_active:
            raise AuthError("User account is invalid or inactive.")

        if not user.mfa_enabled or not user.mfa_secret_encrypted:
            raise AuthError("MFA is not enabled for this user account.")

        secret = decrypt_mfa_secret(user.mfa_secret_encrypted)
        verified = False

        if totp_code:
            verified = verify_totp_code(secret, totp_code)
        elif recovery_code:
            code_hash = hash_recovery_code(recovery_code)
            rec_entry = (
                self.db.query(MFARecoveryCode)
                .filter_by(user_id=user.id, code_hash=code_hash, used=False)
                .first()
            )
            if rec_entry:
                rec_entry.used = True
                rec_entry.used_at = datetime.now(timezone.utc)
                self.db.commit()
                verified = True

        if not verified:
            self._audit(user.id, "MFA_VERIFY_FAILED", ip, "Invalid TOTP or recovery code", success=False)
            raise AuthError("Invalid authenticator code or recovery code.")

        # MFA verification succeeded
        now = datetime.now(timezone.utc)
        user.last_login_at = now
        user.mfa_verified_at = now
        self.db.commit()

        self._audit(user.id, "MFA_LOGIN_SUCCESS", ip, "MFA verification passed", success=True)

        role_name = user.role.name
        permissions = ROLE_PERMISSIONS.get(role_name, [])
        access_token = create_access_token(user.id, user.email, role_name, permissions)
        refresh_raw = create_refresh_token_value()
        self._store_refresh_token(user.id, refresh_raw)

        return {
            "mfa_required": False,
            "access_token": access_token,
            "refresh_token": refresh_raw,
            "token_type": "bearer",
            "must_change_password": user.must_change_password,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": role_name,
                "department": user.department,
                "permissions": permissions,
                "mfa_enabled": True,
            },
        }

    def setup_mfa(self, user: User) -> dict:
        """Initiate MFA setup: generate TOTP secret, QR code, and recovery codes."""
        secret = generate_totp_secret()
        user.mfa_pending_secret_encrypted = encrypt_mfa_secret(secret)
        self.db.commit()

        uri = generate_provisioning_uri(secret, user.email)
        qr_code = generate_qr_code_data_uri(uri)
        raw_recovery_codes = generate_recovery_codes(8)

        self._audit(user.id, "MFA_SETUP_INITIATED", "", "Generated MFA secret & QR code", success=True)

        return {
            "secret": secret,
            "provisioning_uri": uri,
            "qr_code_data_uri": qr_code,
            "recovery_codes": raw_recovery_codes,
        }

    def verify_mfa_setup(self, user: User, totp_code: str, recovery_codes: list[str]) -> dict:
        """Verify 6-digit TOTP code to finalize turning mfa_enabled = True."""
        if not user.mfa_pending_secret_encrypted:
            raise AuthError("MFA setup was not initiated. Please start setup again.")

        secret = decrypt_mfa_secret(user.mfa_pending_secret_encrypted)
        if not verify_totp_code(secret, totp_code):
            self._audit(user.id, "MFA_SETUP_FAILED", "", "Invalid verification code", success=False)
            raise AuthError("Invalid verification code. Check your authenticator app time and 6-digit code.")

        # Save secret as active
        user.mfa_secret_encrypted = user.mfa_pending_secret_encrypted
        user.mfa_pending_secret_encrypted = None
        user.mfa_enabled = True
        now = datetime.now(timezone.utc)
        user.mfa_enabled_at = now
        user.mfa_verified_at = now

        # Store hashed recovery codes
        self.db.query(MFARecoveryCode).filter_by(user_id=user.id).delete()
        for code in recovery_codes:
            ch = hash_recovery_code(code)
            self.db.add(MFARecoveryCode(user_id=user.id, code_hash=ch, used=False))

        self.db.commit()
        self._audit(user.id, "MFA_ENABLED", "", "MFA successfully activated", success=True)

        return {
            "mfa_enabled": True,
            "message": "Authenticator app successfully configured and enabled.",
        }

    def disable_mfa(self, user: User, password: str) -> dict:
        """Disable MFA for account after verifying current password."""
        if not verify_password(password, user.password_hash):
            raise AuthError("Incorrect password.")

        user.mfa_enabled = False
        user.mfa_secret_encrypted = None
        user.mfa_pending_secret_encrypted = None
        user.mfa_enabled_at = None
        self.db.query(MFARecoveryCode).filter_by(user_id=user.id).delete()
        self.db.commit()

        self._audit(user.id, "MFA_DISABLED", "", "MFA disabled by user", success=True)
        return {"mfa_enabled": False, "message": "MFA has been disabled for your account."}

    def regenerate_mfa_recovery_codes(self, user: User) -> dict:
        """Regenerate new recovery codes for user."""
        if not user.mfa_enabled:
            raise AuthError("MFA is not enabled for your account.")

        raw_codes = generate_recovery_codes(8)
        self.db.query(MFARecoveryCode).filter_by(user_id=user.id).delete()
        for code in raw_codes:
            ch = hash_recovery_code(code)
            self.db.add(MFARecoveryCode(user_id=user.id, code_hash=ch, used=False))
        self.db.commit()

        self._audit(user.id, "MFA_RECOVERY_REGENERATED", "", "New recovery codes generated", success=True)
        return {"recovery_codes": raw_codes}

    def reset_user_mfa(self, admin: User, target_user_id: int) -> dict:
        """Admin reset of MFA for a user who lost their authenticator device."""
        target = self.db.get(User, target_user_id)
        if not target:
            raise AuthError("User not found.")

        target.mfa_enabled = False
        target.mfa_secret_encrypted = None
        target.mfa_pending_secret_encrypted = None
        target.mfa_enabled_at = None
        self.db.query(MFARecoveryCode).filter_by(user_id=target_user_id).delete()
        self.db.commit()

        self._audit(admin.id, "MFA_ADMIN_RESET", "", f"Reset MFA for user_id={target_user_id}", success=True)
        return {"message": f"MFA state successfully reset for user {target.email}."}

    # ------------------------------------------------------------------
    # Change initial / forced password
    # ------------------------------------------------------------------
    def change_initial_password(
        self,
        user: User,
        current_temp_password: str,
        new_password: str,
        confirm_password: str,
    ) -> dict:
        if new_password != confirm_password:
            raise AuthError("Passwords do not match.")
        try:
            validate_password_policy(new_password, user.email)
        except PasswordPolicyError as exc:
            raise AuthError(str(exc)) from exc

        if not verify_password(current_temp_password, user.password_hash):
            raise AuthError("Current temporary password is incorrect.")

        if new_password == current_temp_password:
            raise AuthError("New password must be different from the temporary password.")

        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        user.temp_password_expires_at = None
        self.db.commit()

        # Revoke all existing refresh tokens
        self.db.query(RefreshToken).filter_by(user_id=user.id).update({"revoked": True})
        self.db.commit()

        self._audit(user.id, "PASSWORD_CHANGED", "", "Initial password change completed", success=True)

        role_name = user.role.name
        permissions = ROLE_PERMISSIONS.get(role_name, [])
        access_token = create_access_token(user.id, user.email, role_name, permissions)
        refresh_raw = create_refresh_token_value()
        self._store_refresh_token(user.id, refresh_raw)

        return {
            "access_token": access_token,
            "refresh_token": refresh_raw,
            "token_type": "bearer",
            "must_change_password": False,
            "message": "Password changed successfully.",
        }

    # ------------------------------------------------------------------
    # Admin: create user
    # ------------------------------------------------------------------
    def create_user(
        self,
        admin: User,
        email: str,
        full_name: str,
        role_name: str,
        department: Optional[str] = None,
        faculty_id: Optional[int] = None,
    ) -> dict:
        if role_name not in VALID_ROLES:
            raise AuthError(f"Invalid role '{role_name}'. Valid roles: {VALID_ROLES}")

        existing = self.db.query(User).filter_by(email=email.lower()).first()
        if existing:
            raise AuthError(f"A user with email '{email}' already exists.")

        role = self.db.query(Role).filter_by(name=role_name).first()
        if not role:
            raise AuthError(f"Role '{role_name}' not found in database. Run seed first.")

        temp_pw = generate_temp_password()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.settings.TEMP_PASSWORD_EXPIRY_HOURS)

        user = User(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            role_id=role.id,
            department=department,
            faculty_id=faculty_id,
            is_active=True,
            password_hash=hash_password(temp_pw),
            must_change_password=True,
            temp_password_expires_at=expires_at,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self._audit(admin.id, "USER_CREATED", "", f"Created user {email} with role {role_name}", success=True)

        return {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": role_name,
            "department": department,
            "must_change_password": True,
            "temp_password_expires_hours": self.settings.TEMP_PASSWORD_EXPIRY_HOURS,
            "temporary_password": temp_pw,
            "_warning": "Display once only. This password will not be shown again.",
        }

    # ------------------------------------------------------------------
    # Admin: list / deactivate users
    # ------------------------------------------------------------------
    def list_users(self) -> list[dict]:
        users = self.db.query(User).all()
        return [_user_dict(u) for u in users]

    def deactivate_user(self, admin: User, user_id: int) -> None:
        user = self.db.get(User, user_id)
        if not user:
            raise AuthError("User not found.")
        if user.id == admin.id:
            raise AuthError("Cannot deactivate your own account.")
        user.is_active = False
        self.db.commit()
        self._audit(admin.id, "USER_DEACTIVATED", "", f"Deactivated user_id={user_id}", success=True)

    def activate_user(self, admin: User, user_id: int) -> None:
        user = self.db.get(User, user_id)
        if not user:
            raise AuthError("User not found.")
        user.is_active = True
        self.db.commit()
        self._audit(admin.id, "USER_ACTIVATED", "", f"Activated user_id={user_id}", success=True)

    def force_password_reset(self, admin: User, user_id: int) -> dict:
        user = self.db.get(User, user_id)
        if not user:
            raise AuthError("User not found.")
        temp_pw = generate_temp_password()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.settings.TEMP_PASSWORD_EXPIRY_HOURS)
        user.password_hash = hash_password(temp_pw)
        user.must_change_password = True
        user.temp_password_expires_at = expires_at
        self.db.query(RefreshToken).filter_by(user_id=user.id).update({"revoked": True})
        self.db.commit()
        self._audit(admin.id, "PASSWORD_FORCE_RESET", "", f"Force reset for user_id={user_id}", success=True)
        return {
            "user_id": user.id,
            "email": user.email,
            "temporary_password": temp_pw,
            "_warning": "Display once only.",
        }

    # ------------------------------------------------------------------
    # Refresh token storage
    # ------------------------------------------------------------------
    def _store_refresh_token(self, user_id: int, raw_token: str) -> None:
        settings = self.settings
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        rt = RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(rt)
        self.db.commit()

    # ------------------------------------------------------------------
    # Audit helper
    # ------------------------------------------------------------------
    def _audit(self, user_id: Optional[int], action: str, ip: str, details: str, success: bool) -> None:
        log = UserAuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip or None,
            details=details[:500] if details else None,
            success=success,
        )
        self.db.add(log)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()


def _user_dict(u: User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role.name if u.role else None,
        "department": u.department,
        "is_active": u.is_active,
        "must_change_password": u.must_change_password,
        "mfa_enabled": u.mfa_enabled,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }