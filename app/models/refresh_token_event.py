from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text
from sqlalchemy.sql import func
from app.db import Base

class RefreshTokenEvent(Base):
    __tablename__ = "refresh_token_events"

    id = Column(Integer, primary_key=True, index=True)
    refresh_token_id = Column(Integer, ForeignKey("refresh_tokens.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(32), nullable=False)  # e.g. "rotation", "reuse_detected", "logout"
    ip = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # free-form JSON/text if needed
    created_at = Column(DateTime(timezone=False), server_default=func.datetime("now"))
