# app/core/auth.py
import secrets
from datetime import datetime, timedelta
from passlib.context import CryptContext
from app.models.refresh_token import RefreshToken
from app.db import SessionLocal

# reuse secure hashing; Argon2 is good. Adjust to your security.py if needed.
pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")

def generate_refresh_token_str(length_bytes: int = 48) -> str:
    return secrets.token_urlsafe(length_bytes)

def hash_refresh_token(token: str) -> str:
    return pwd_ctx.hash(token)

def verify_refresh_token_hash(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def store_refresh_token(db, user_id: int, token_plain: str, expires_minutes: int = 60*24*30):
    token_hash = hash_refresh_token(token_plain)
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
    rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt

def revoke_refresh_token(db, rt: RefreshToken):
    rt.revoked = True
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt
