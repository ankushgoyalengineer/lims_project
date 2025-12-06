# app/core/config.py
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
ENV = os.getenv("ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

# Runtime security toggles
EXPOSE_REFRESH_IN_BODY = os.getenv("EXPOSE_REFRESH_IN_BODY", "true").lower() == "true"
REVOKE_ALL_ON_REFRESH_REUSE = os.getenv("REVOKE_ALL_ON_REFRESH_REUSE", "true").lower() == "true"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")  # "strict", "lax", or "none"

# Token TTL (optional override)
REFRESH_TOKEN_TTL_SECONDS = int(os.getenv("REFRESH_TOKEN_TTL_SECONDS", 60 * 60 * 24 * 30))
