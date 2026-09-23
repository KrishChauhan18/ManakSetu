import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Any, Dict
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Cryptographic Libraries ---
try:
    from jose import jwt, JWTError
except ImportError:
    jwt = None
    JWTError = Exception

try:
    import bcrypt as _bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:
    _bcrypt = None  # type: ignore
    _BCRYPT_AVAILABLE = False

# We intentionally do NOT use passlib.CryptContext here because passlib's
# internal bcrypt compatibility detection (`detect_wrap_bug`) passes a
# password > 72 bytes to bcrypt 5.x, which now enforces the limit at the C
# level and raises ValueError, making CryptContext fail to initialize.
# Instead we call bcrypt directly with proper pre-truncation.


def _safe_encode(password: str) -> bytes:
    """Encode and truncate password to bcrypt's 72-byte hard limit."""
    return password.encode("utf-8")[:72]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Cryptographically verify a plain password against a stored bcrypt hash.
    Pre-truncates to 72 bytes to satisfy bcrypt 5.x strict limit.
    """
    if not plain_password or not hashed_password:
        return False

    if not _BCRYPT_AVAILABLE:
        logger.critical("bcrypt is not available — cannot verify password.")
        return False

    try:
        return _bcrypt.checkpw(_safe_encode(plain_password), hashed_password.encode("utf-8"))
    except Exception as exc:
        logger.error(f"Password verification error: {exc}")
        return False


def get_password_hash(password: str) -> str:
    """
    Generate a salted bcrypt hash for a plaintext password.
    Raises RuntimeError if bcrypt is unavailable.
    """
    if not password:
        raise ValueError("Cannot hash an empty password.")

    if not _BCRYPT_AVAILABLE:
        raise RuntimeError(
            "CRITICAL SECURITY ERROR: 'bcrypt' is not installed. Cannot hash passwords."
        )

    try:
        salt = _bcrypt.gensalt(rounds=12)
        return _bcrypt.hashpw(_safe_encode(password), salt).decode("utf-8")
    except Exception as exc:
        logger.error(f"Error generating bcrypt hash: {exc}")
        raise RuntimeError(f"Password hashing failed: {exc}") from exc


def create_access_token(
    subject: Union[str, int, Any],
    role: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a cryptographically signed JWT using HMAC-SHA256 (HS256).

    SECURITY NOTE: The insecure base64 fallback has been fully removed.
    If the signing library or SECRET_KEY is unavailable this raises immediately.
    """
    if jwt is None:
        logger.critical("Fatal: 'python-jose' is not installed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cryptographic provider unavailable for token signing.",
        )

    if not settings.SECRET_KEY or len(settings.SECRET_KEY.strip()) < 32:
        logger.critical("Fatal: SECRET_KEY is not configured with adequate strength.")
        raise RuntimeError(
            "CRITICAL SECURITY ERROR: SECRET_KEY is unconfigured or too short."
        )

    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode: Dict[str, Any] = {
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "sub": str(subject),
        "role": str(role),
    }

    if additional_claims and isinstance(additional_claims, dict):
        for k, v in additional_claims.items():
            if k not in to_encode:
                to_encode[k] = v

    try:
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    except Exception as exc:
        logger.error(f"Failed to sign JWT: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token signature generation failed.",
        ) from exc
