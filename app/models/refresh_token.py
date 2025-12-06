# app/models/refresh_token.py
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)   # changed to 64
    device_id = Column(String(128), nullable=True, index=True)                 # keep index
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
