"""Password hashing using bcrypt via passlib."""
from __future__ import annotations
import re
import secrets
import string

import bcrypt

# Workaround for passlib + bcrypt >= 4.1.0 compatibility bug
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("About", (), {"__version__": getattr(bcrypt, "__version__", "4.0.0")})

from passlib.context import CryptContext

# passlib handles bcrypt; bcrypt library installed as backend
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ------------------------------------------------------------------
# Hash / verify
# ------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of plain-text password. Never stores plaintext."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against stored bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


# ------------------------------------------------------------------
# Temporary password generation
# ------------------------------------------------------------------

_UPPER = string.ascii_uppercase
_LOWER = string.ascii_lowercase
_DIGITS = string.digits
_SPECIAL = "!@#$%^&*()-_=+"

def generate_temp_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure temporary password.
    Guarantees at least one of each character class.
    Never produces predictable sequences.
    """
    if length < 8:
        length = 16
    # Guarantee one of each required class
    required = [
        secrets.choice(_UPPER),
        secrets.choice(_UPPER),
        secrets.choice(_LOWER),
        secrets.choice(_LOWER),
        secrets.choice(_DIGITS),
        secrets.choice(_DIGITS),
        secrets.choice(_SPECIAL),
        secrets.choice(_SPECIAL),
    ]
    pool = _UPPER + _LOWER + _DIGITS + _SPECIAL
    remainder = [secrets.choice(pool) for _ in range(length - len(required))]
    combined = required + remainder
    secrets.SystemRandom().shuffle(combined)
    return "".join(combined)


# ------------------------------------------------------------------
# Password policy validation
# ------------------------------------------------------------------

class PasswordPolicyError(ValueError):
    pass


def validate_password_policy(password: str, email: str = "") -> None:
    """
    Raise PasswordPolicyError if password does not meet requirements.
    Minimum 12 characters, upper, lower, digit, special char.
    """
    if len(password) < 12:
        raise PasswordPolicyError("Password must be at least 12 characters.")
    if not re.search(r"[A-Z]", password):
        raise PasswordPolicyError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise PasswordPolicyError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise PasswordPolicyError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()_\-=+\[\]{};:,.<>?/|\\]", password):
        raise PasswordPolicyError("Password must contain at least one special character.")

    bad_patterns = ["password", "admin", "qwerty", "123456", "letmein", "welcome"]
    lc = password.lower()
    for pat in bad_patterns:
        if pat in lc:
            raise PasswordPolicyError(f"Password contains a disallowed pattern: '{pat}'.")
    if email:
        local = email.split("@")[0].lower()
        if len(local) > 3 and local in lc:
            raise PasswordPolicyError("Password must not contain your email address.")