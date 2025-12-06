# app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.db import engine, Base
from app.core.config import ENV

# import limiter instance (decides whether middleware is added)
from app.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.responses import PlainTextResponse

# routers
from app.routes import users as users_router
from app.routes import auth as auth_router
from app.routes import samples as samples_router
from app.routes import projects as projects_router

app = FastAPI(title="LIMS Backend")

# attach limiter instance on app.state so routes can reference it if needed
app.state.limiter = limiter

# add middleware only when limiter is enabled to avoid race conditions
if getattr(limiter, "enabled", True):
    app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return PlainTextResponse("Too many requests", status_code=429)

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
app.include_router(projects_router.router)

# Minimal CORS for dev. Restrict origin in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes,
    )
    # ensure single named scheme
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})[
        "AccessTokenAuth"
    ] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
