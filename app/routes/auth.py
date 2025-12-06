# app/routes/auth.py
from fastapi import (
    APIRouter, Depends, HTTPException, status,
    Request, Response, Cookie, Query
)
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import logging
import json

from pydantic import BaseModel, ConfigDict

# correct limiter import (NO circular imports)
from app.limiter import limiter

from app.schemas import TokenOut, TokenIn
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token_plain,
    hash_refresh_token_for_db,
)
from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.refresh_token_event import RefreshTokenEvent
from app.core.config import (
    EXPOSE_REFRESH_IN_BODY,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    REFRESH_TOKEN_TTL_SECONDS,
    REVOKE_ALL_ON_REFRESH_REUSE,
)

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

REFRESH_COOKIE_NAME = "refresh_token"


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _set_refresh_cookie(response: Response, token_plain: str, max_age: int = REFRESH_TOKEN_TTL_SECONDS):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token_plain,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
        max_age=max_age,
    )


def _clear_refresh_cookie(response: Response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")


def _capture_device_id(request: Optional[Request]) -> Optional[str]:
    if not request:
        return None
    d = request.headers.get("x-device-id") or request.headers.get("user-agent")
    return d[:128] if d else None


def _make_event(
    db: Session,
    refresh_token_id: Optional[int],
    user_id: Optional[int],
    event_type: str,
    request: Optional[Request] = None,
    details: Optional[dict] = None,
):
    try:
        ip = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
    except Exception:
        ip = None
        ua = None

    ev = RefreshTokenEvent(
        refresh_token_id=refresh_token_id,
        user_id=user_id,
        event_type=event_type,
        ip=ip,
        user_agent=ua,
        details=json.dumps(details) if details else None,
    )
    db.add(ev)


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------

@router.post("/token", response_model=TokenOut)
@limiter.limit("10/minute")     # prevent brute-force login
def login_for_tokens(payload: TokenIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token, expires_in = create_access_token(subject=str(user.id))

    device_id = _capture_device_id(request)

    refresh_plain, refresh_expires_at = create_refresh_token_plain()
    token_hash = hash_refresh_token_for_db(refresh_plain)

    rt = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        device_id=device_id,
        expires_at=refresh_expires_at,
    )
    db.add(rt)

    db.flush()
    _make_event(db, rt.id, user.id, "issue", request, {"note": "initial login"})
    db.commit()
    db.refresh(rt)

    _set_refresh_cookie(response, refresh_plain)

    body = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }
    if EXPOSE_REFRESH_IN_BODY:
        body["refresh_token"] = refresh_plain
    return body


# ------------------------------------------------------------
# REFRESH ROTATION
# ------------------------------------------------------------

@router.post("/token/refresh", response_model=TokenOut)
@limiter.limit("30/minute")
def rotate_refresh_token(
    request: Request,
    response: Response,
    payload: Optional[dict] = None,
    refresh_token_cookie: Optional[str] = Cookie(None, alias=REFRESH_COOKIE_NAME),
    db: Session = Depends(get_db),
):
    rt_plain = refresh_token_cookie or (payload.get("refresh_token") if payload else None)
    if not rt_plain:
        raise HTTPException(status_code=400, detail="refresh_token required")

    token_hash = hash_refresh_token_for_db(rt_plain)
    rt_obj = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if not rt_obj:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # reuse detection
    if rt_obj.revoked:
        _make_event(db, rt_obj.id, rt_obj.user_id, "reuse_detected", request, {"note": "revoked token presented"})
        if REVOKE_ALL_ON_REFRESH_REUSE:
            db.query(RefreshToken).filter(
                RefreshToken.user_id == rt_obj.user_id,
                RefreshToken.revoked == False
            ).update({"revoked": True}, synchronize_session=False)
        else:
            rt_obj.revoked = True
            db.add(rt_obj)

        db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh token revoked or reused")

    # expiration
    if rt_obj.expires_at and rt_obj.expires_at < datetime.utcnow():
        rt_obj.revoked = True
        db.add(rt_obj)
        _make_event(db, rt_obj.id, rt_obj.user_id, "expired", request)
        db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # rotate token
    try:
        rt_obj.revoked = True
        db.add(rt_obj)

        new_plain, new_expires_at = create_refresh_token_plain()
        new_hash = hash_refresh_token_for_db(new_plain)

        device_id = rt_obj.device_id or _capture_device_id(request)

        new_rt = RefreshToken(
            user_id=rt_obj.user_id,
            token_hash=new_hash,
            device_id=device_id,
            expires_at=new_expires_at,
        )
        db.add(new_rt)

        db.flush()

        _make_event(db, rt_obj.id, rt_obj.user_id, "rotation_old_revoked", request, {"old_id": rt_obj.id, "new_id": new_rt.id})
        _make_event(db, new_rt.id, new_rt.user_id, "rotation_new_issued", request, {"new_id": new_rt.id})

        db.commit()
        db.refresh(new_rt)

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not rotate token")

    _set_refresh_cookie(response, new_plain)

    access_token, expires_in = create_access_token(subject=str(rt_obj.user_id))
    body = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }
    if EXPOSE_REFRESH_IN_BODY:
        body["refresh_token"] = new_plain
    return body


# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    payload: Optional[dict] = None,
    refresh_token_cookie: Optional[str] = Cookie(None, alias=REFRESH_COOKIE_NAME),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rt_plain = refresh_token_cookie or (payload.get("refresh_token") if payload else None)

    if not rt_plain:
        _clear_refresh_cookie(response)
        return {"detail": "ok"}

    token_hash = hash_refresh_token_for_db(rt_plain)
    rt_obj = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.user_id == current_user.id
    ).first()

    if not rt_obj:
        _clear_refresh_cookie(response)
        _make_event(db, None, current_user.id, "logout_unknown_token", request)
        db.commit()
        return {"detail": "ok"}

    rt_obj.revoked = True
    db.add(rt_obj)
    _make_event(db, rt_obj.id, current_user.id, "logout_token_revoked", request)
    db.commit()

    _clear_refresh_cookie(response)
    return {"detail": "ok"}


# ------------------------------------------------------------
# AUDIT EVENTS
# ------------------------------------------------------------

@router.get("/token/events")
def list_refresh_token_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
):
    events = (
        db.query(RefreshTokenEvent)
        .filter(RefreshTokenEvent.user_id == current_user.id)
        .order_by(RefreshTokenEvent.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    out = []
    for e in events:
        try:
            details = json.loads(e.details) if e.details else None
        except Exception:
            details = None

        out.append(
            {
                "id": e.id,
                "refresh_token_id": e.refresh_token_id,
                "event_type": e.event_type,
                "ip": e.ip,
                "user_agent": e.user_agent,
                "details": details,
                "created_at": e.created_at,
            }
        )
    return out


# ------------------------------------------------------------
# SESSION LISTING AND REVOCATION
# ------------------------------------------------------------

class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: Optional[str]
    revoked: bool
    created_at: datetime
    expires_at: Optional[datetime]


@router.get("/token/sessions", response_model=list[SessionOut])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    q = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == current_user.id)
        .order_by(RefreshToken.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return q.all()


@router.delete("/token/sessions/{session_id}", status_code=204)
def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rt = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.id == session_id,
            RefreshToken.user_id == current_user.id
        )
        .first()
    )

    if not rt:
        raise HTTPException(status_code=404, detail="session not found")

    if not rt.revoked:
        rt.revoked = True
        db.add(rt)
        _make_event(db, rt.id, current_user.id, "manual_revoke")
        db.commit()

    return Response(status_code=204)
