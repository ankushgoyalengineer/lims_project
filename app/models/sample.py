from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.db import Base

class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(128), unique=True, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    sample_type = Column(String(100), nullable=True)
    # database column name (Postgres uses JSON type; tests use SQLite but JSON column will be text)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    project = relationship("Project", back_populates="samples")

    @property
    def metadata_dict(self):
        return self.metadata_json if self.metadata_json is not None else {}
