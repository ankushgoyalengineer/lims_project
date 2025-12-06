# tests/test_refresh_rotation.py
import hashlib
import json
import sqlite3
import requests

BASE = "http://127.0.0.1:8000"

def test_rotate_and_detect_reuse():
    s1 = requests.Session()
    r = s1.post(f"{BASE}/token", json={"username":"test@example.com","password":"abc12345"})
    assert r.status_code == 200
    old_cookie = s1.cookies.get("refresh_token")
    assert old_cookie

    # rotate in same session (valid)
    r_rotate = s1.post(f"{BASE}/token/refresh")
    assert r_rotate.status_code == 200
    body = r_rotate.json()
    assert "access_token" in body

    # attempt reuse from another session with old cookie
    s2 = requests.Session()
    s2.cookies.set("refresh_token", old_cookie, domain="127.0.0.1", path="/")
    r_reuse = s2.post(f"{BASE}/token/refresh")
    assert r_reuse.status_code == 401
    assert r_reuse.json().get("detail") in ("Refresh token revoked or reused", "Invalid refresh token")

    # optional DB checks (sqlite local dev)
    h = hashlib.sha256(old_cookie.encode()).hexdigest()
    c = sqlite3.connect("dev.db")
    rows = c.execute("SELECT id, user_id, revoked FROM refresh_tokens WHERE token_hash=?", (h,)).fetchall()
    c.close()
    assert rows and rows[0][2] == 1
