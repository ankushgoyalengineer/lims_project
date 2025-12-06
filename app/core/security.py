# app/core/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional, Tuple
import secrets
import hashlib

from app.core.config import SECRET_KEY

pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day default
REFRESH_TOKEN_EXPIRE_DAYS = 30  # refresh token lifetime

# ----- password helpers -----
def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

# ----- access token helpers -----
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> Tuple[str, int]:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": subject, "exp": int(expire.timestamp())}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, int((expire - datetime.utcnow()).total_seconds())

def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        return sub
    except JWTError:
        return None

# ----- refresh token helpers -----
def _hash_refresh_token(token: str) -> str:
    # store SHA256 hex digest of the token
    h = hashlib.sha256()
    h.update(token.encode("utf-8"))
    return h.hexdigest()

def create_refresh_token_plain(expires_days: int = REFRESH_TOKEN_EXPIRE_DAYS) -> Tuple[str, datetime]:
    """
    Produce a cryptographically secure random refresh token string and expiry datetime.
    Returns (plaintext_token, expires_at)
    """
    token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    return token, expires_at

def hash_refresh_token_for_db(plain_token: str) -> str:
    return _hash_refresh_token(plain_token)

def verify_refresh_token_plain_against_hash(plain_token: str, token_hash: str) -> bool:
    return _hash_refresh_token(plain_token) == token_hash
