# app/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
import jwt
from typing import Optional
from app.core.config import SECRET_KEY, ENV

def _user_key_func(request: Request) -> str:
    """
    Prefer authenticated user id (sub) from Bearer access token.
    Fallback to client IP when token missing or invalid.
    Key format: "user:<id>" or "ip:<addr>".
    """
    auth = request.headers.get("authorization")
    if auth:
        parts = auth.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                sub = payload.get("sub")
                if sub:
                    return f"user:{sub}"
            except Exception:
                # invalid token -> fall back to IP
                pass
    # last-resort: IP
    return f"ip:{get_remote_address(request)}"

# enable limiter except in testing where you may want it off
_enabled = (ENV != "testing")
limiter = Limiter(key_func=_user_key_func, enabled=_enabled)
