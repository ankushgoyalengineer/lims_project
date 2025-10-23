# app/models/sample.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.db import Base

class Sample(Base):
    __tablename__ = "samples"
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(128), unique=True, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    sample_type = Column(String(100), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)  # renamed attribute
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", backref="samples")
