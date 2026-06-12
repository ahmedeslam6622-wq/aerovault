"""
Authentication core.

- All users: username + password → JWT token
- Superuser ONLY: username + password + 6-digit TOTP code (changes every 30 seconds)
  TOTP secret is set once at first run and printed as a QR code URI.
  Scan it with Google Authenticator / Authy — done.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
import pyotp
import os

# ── Config ────────────────────────────────────────────────────────────────
SECRET_KEY      = os.getenv("JWT_SECRET", "aerovault-dev-secret-change-in-production-abc123xyz")
ALGORITHM       = "HS256"
ACCESS_TOKEN_TTL = 60 * 8   # 8 hours in minutes — one shift

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ──────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_TTL) -> str:
    payload = data.copy()
    expire  = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ── TOTP helpers (Superuser only) ─────────────────────────────────────────

def generate_totp_secret() -> str:
    """Generate a new TOTP secret for a superuser account."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str) -> str:
    """Returns the otpauth:// URI to encode as a QR code."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name="AeroVault")


def verify_totp(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code. Allows ±1 window (30s each side)."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def get_current_totp(secret: str) -> str:
    """Dev helper — generate current TOTP code for testing."""
    return pyotp.TOTP(secret).now()
