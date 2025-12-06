# tests/test_refresh_sessions.py
import hashlib
import json
import sqlite3
import requests

BASE = "http://127.0.0.1:8000"

def test_rotate_reuse_and_sessions():
    s1 = requests.Session()
    r = s1.post(f"{BASE}/token", json={"username":"test@example.com","password":"abc12345"})
    assert r.status_code == 200
    old_cookie = s1.cookies.get("refresh_token")
    assert old_cookie

    # rotate
    r_rotate = s1.post(f"{BASE}/token/refresh")
    assert r_rotate.status_code == 200

    # reuse attempt from separate session using old cookie
    s2 = requests.Session()
    s2.cookies.set("refresh_token", old_cookie, domain="127.0.0.1", path="/")
    r_reuse = s2.post(f"{BASE}/token/refresh")
    assert r_reuse.status_code == 401

    # call sessions endpoint using new access token
    access = r_rotate.json()["access_token"]
    hdr = {"Authorization": f"Bearer {access}"}
    r_sessions = requests.get(f"{BASE}/token/sessions", headers=hdr)
    assert r_sessions.status_code == 200
    sessions = r_sessions.json()
    assert isinstance(sessions, list)

    # revoke one session via API (pick first non-revoked)
    target = next((s for s in sessions if not s.get("revoked")), None)
    if target:
        r_revoke = requests.delete(f"{BASE}/token/sessions/{target['id']}", headers=hdr)
        assert r_revoke.status_code == 200
