"""TOTP Multi-Factor Authentication security utilities."""
from __future__ import annotations
import base64
import hashlib
import io
import secrets
import pyotp
import qrcode
from cryptography.fernet import Fernet

from ..config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    secret_bytes = (settings.JWT_SECRET_KEY or "agent34-fallback-secret-key-32bytes!!").encode()
    key_bytes = hashlib.sha256(secret_bytes).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_mfa_secret(secret: str) -> str:
    """Encrypt TOTP base32 secret before DB persistence."""
    f = _get_fernet()
    return f.encrypt(secret.encode()).decode()


def decrypt_mfa_secret(encrypted_secret: str) -> str:
    """Decrypt stored TOTP base32 secret."""
    f = _get_fernet()
    return f.decrypt(encrypted_secret.encode()).decode()


def generate_totp_secret() -> str:
    """Generate a random base32 secret for TOTP authenticator app."""
    return pyotp.random_base32()


def generate_provisioning_uri(secret: str, email: str, issuer_name: str = "Agent34 Result Analysis") -> str:
    """Create otpauth:// URI for authenticator apps."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer_name)


def generate_qr_code_data_uri(provisioning_uri: str) -> str:
    """Render QR code PNG as base64 data URI."""
    img = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    try:
        img.save(buf, format="PNG")
    except TypeError:
        img.save(buf)
    b64_png = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64_png}"


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify 6-digit TOTP code against base32 secret (tolerates +/- 30s clock skew)."""
    if not code or len(code.strip()) != 6:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip(), valid_window=1)


def generate_recovery_codes(count: int = 8) -> list[str]:
    """Generate 8 single-use recovery codes in XXXX-XXXX format."""
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(4).upper()
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes


def hash_recovery_code(code: str) -> str:
    """Hash normalized recovery code with SHA-256."""
    normalized = code.strip().upper().replace("-", "")
    return hashlib.sha256(normalized.encode()).hexdigest()
