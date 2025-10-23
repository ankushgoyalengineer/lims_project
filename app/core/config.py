# app/core/config.py
from pathlib import Path
from dotenv import load_dotenv
import os

# load .env from project root
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
ENV = os.getenv("ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
