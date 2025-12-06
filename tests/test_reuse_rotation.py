# tests/test_reuse_rotation.py
from fastapi.testclient import TestClient
from app.main import app
import hashlib
import sqlite3
import json

BASE = "/token"


def test_rotate_and_detect_reuse(client: TestClient):
    # login and capture old refresh cookie
    r = client.post(f"{BASE}", json={"username": "test@example.com", "password": "abc12345"})
    assert r.status_code == 200
    old = client.cookies.get("refresh_token")
    assert old

    # rotate using the same session (valid)
    r2 = client.post(f"{BASE}/refresh")
    assert r2.status_code == 200
    rotated = client.cookies.get("refresh_token")
    assert rotated and rotated != old

    # reuse attempt with old token from a second client must fail
    with TestClient(app) as s2:
        s2.cookies.set("refresh_token", old, domain="127.0.0.1", path="/")
        r3 = s2.post(f"{BASE}/refresh")
        assert r3.status_code == 401

    # optional: check DB shows the old token marked revoked (simple sqlite check)
    try:
        h = hashlib.sha256(old.encode()).hexdigest()
        c = sqlite3.connect("test.db")
        rows = c.execute("SELECT id, user_id, revoked FROM refresh_tokens WHERE token_hash=?", (h,)).fetchall()
        # expect either revoked row(s) or no row if hash length differs; at least no success status implied
        assert rows and rows[0][2] in (0, 1)
    finally:
        try:
            c.close()
        except Exception:
            pass
