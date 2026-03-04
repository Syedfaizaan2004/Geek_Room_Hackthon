"""
utils/security.py — Cryptographic utilities for authentication.

Provides:
  1. hash_dob(dob)          — SHA-256 pre-hash → bcrypt hash
  2. verify_dob(raw, hash)  — constant-time DOB verification
  3. create_access_token()  — sign a JWT with expiry
  4. verify_token()         — decode and validate a JWT

BCRYPT COMPATIBILITY NOTE:
──────────────────────────
passlib 1.7.4 is incompatible with bcrypt >= 4.0 (API change: no __about__).
We call the `bcrypt` library directly (hashpw / checkpw) to avoid the issue.

SHA-256 PRE-HASHING:
─────────────────────
bcrypt has a hard 72-byte input limit. We pre-hash the DOB with SHA-256 first:

  raw_dob ──► SHA-256 ──► 32 raw bytes (always, regardless of input) ──► bcrypt
                                              ^ safely under 72-byte limit

Using raw bytes (not hex string) from SHA-256 gives 32 bytes — half of 64-char
hex. Either works (32 bytes or 64 chars are both < 72), but raw bytes is cleaner.
"""

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt as _bcrypt
from jose import JWTError, jwt

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DOB_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BCRYPT_ROUNDS = 12   # Work factor — increase to 14 in production if latency allows


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _sha256_bytes(value: str) -> bytes:
    """
    Return the raw 32-byte SHA-256 digest of a UTF-8 string.

    bcrypt accepts raw bytes. 32 bytes is safely below bcrypt's 72-byte limit.
    SHA-256 → 32 bytes is deterministic and length-independent of the input.
    """
    return hashlib.sha256(value.encode("utf-8")).digest()   # raw bytes, not hex


def _validate_dob(dob: str) -> None:
    """
    Raise ValueError if DOB is not a valid YYYY-MM-DD past date.
    """
    if not _DOB_PATTERN.match(dob):
        raise ValueError("date_of_birth must be in YYYY-MM-DD format")
    try:
        from datetime import date
        parsed = date.fromisoformat(dob)
        if parsed.year < 1900 or parsed > date.today():
            raise ValueError("date_of_birth must be a valid past date after 1900")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid date_of_birth: {exc}") from exc


# ---------------------------------------------------------------------------
# DOB hashing  (SHA-256 → bcrypt, direct bcrypt API)
# ---------------------------------------------------------------------------
def hash_dob(dob: str) -> str:
    """
    Hash a date-of-birth string using SHA-256 pre-hash + bcrypt.

    Pipeline:
        raw_dob → validate → SHA-256 digest (32 bytes) → bcrypt → stored hash

    Args:
        dob: Date string in YYYY-MM-DD format.

    Returns:
        bcrypt hash string (60 chars) safe to store in the database.

    Raises:
        ValueError: If dob format is invalid.
    """
    _validate_dob(dob)
    dob_bytes = _sha256_bytes(dob)                    # 32 bytes — safe for bcrypt
    salt = _bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = _bcrypt.hashpw(dob_bytes, salt)          # bcrypt direct API
    return hashed.decode("utf-8")                     # store as UTF-8 string in DB


def verify_dob(raw_dob: str, hashed_dob: str) -> bool:
    """
    Verify a raw DOB against its stored bcrypt hash.

    Pipeline:
        raw_dob → SHA-256 digest (32 bytes) → bcrypt.checkpw → True/False

    Args:
        raw_dob:    Plain-text date string from the login request.
        hashed_dob: bcrypt hash string stored in the database.

    Returns:
        True if DOB matches, False on any failure.
        Never raises — returns False to prevent information leakage.
    """
    try:
        if not _DOB_PATTERN.match(raw_dob):
            return False
        dob_bytes = _sha256_bytes(raw_dob)
        return _bcrypt.checkpw(dob_bytes, hashed_dob.encode("utf-8"))
    except Exception as exc:
        logger.warning("DOB verification error", extra={"error": str(exc)})
        return False


# ---------------------------------------------------------------------------
# JWT token helpers  (python-jose, unaffected by passlib issue)
# ---------------------------------------------------------------------------
def create_access_token(data: dict[str, Any]) -> tuple[str, int]:
    """
    Sign a JWT access token.

    Args:
        data: Payload dict — typically {"sub": unique_user_id}.
              NEVER include DOB, hashes, or other sensitive data.

    Returns:
        Tuple of (jwt_string, expires_in_seconds).
    """
    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

    payload = {
        **data,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",           # prevents refresh tokens being accepted here
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, expire_minutes * 60


def verify_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: Raw JWT string from the Authorization header.

    Returns:
        Decoded payload dict.

    Raises:
        ValueError: On expired, malformed, or wrong-type tokens.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise ValueError(f"Invalid or expired token: {exc}") from exc

    if payload.get("type") != "access":
        raise ValueError("Token type is not 'access'")

    if not payload.get("sub"):
        raise ValueError("Token missing 'sub' claim")

    return payload
