# app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

# Create engine. For SQLite file or memory, SQLAlchemy will handle the URL.
engine = create_engine(DATABASE_URL, future=True, echo=False, pool_pre_ping=True)

# Session factory used by application code
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Declarative base
Base = declarative_base()

# Dependency generator for FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
