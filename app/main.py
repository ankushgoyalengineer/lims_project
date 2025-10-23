import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base
from app.core.config import ENV

# routers
from app.routes import users as users_router
from app.routes import auth as auth_router
from app.routes import samples as samples_router

app = FastAPI(title="LIMS Backend")

# Development-only: create tables automatically (use Alembic in production)
@app.on_event("startup")
def startup():
    if ENV == "development":
        Base.metadata.create_all(bind=engine)
        logging.info("Created tables (development).")

# Basic health check
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

# Register routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(samples_router.router)

# Minimal CORS for dev. Restrict origin in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
