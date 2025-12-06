# app/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security
from sqlalchemy.orm import Session
from typing import Optional

from app.db import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User

# single HTTP bearer scheme used for OpenAPI and route security
bearer = HTTPBearer(auto_error=False, scheme_name="AccessTokenAuth")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate Authorization: Bearer <token>. Tie this dependency to the
    AccessTokenAuth OpenAPI scheme by using Security(bearer).
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    subject = decode_access_token(token)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == int(subject)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
