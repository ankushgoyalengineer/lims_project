# tests/test_refresh_integration.py
import hashlib
import json
import sqlite3
import time

import requests

BASE = "http://127.0.0.1:8000"
LOGIN_PAYLOAD = {"username": "test@example.com", "password": "abc12345"}
# user-agent we'll use as "device id"
DEVICE_UA = "pytest-refresh-integration/1.0"

def query_db(sql, params=()):
    c = sqlite3.connect("dev.db")
    rows = c.execute(sql, params).fetchall()
    c.close()
    return rows

def test_refresh_rotation_and_reuse():
    s1 = requests.Session()
    # login with explicit user-agent header so device_id is known
    r = s1.post(f"{BASE}/token", json=LOGIN_PAYLOAD, headers={"User-Agent": DEVICE_UA})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    old_cookie = s1.cookies.get("refresh_token")
    assert old_cookie, "no refresh cookie set on login"

    # rotate in same session -> should succeed and set new cookie
    r_rot = s1.post(f"{BASE}/token/refresh", headers={"User-Agent": DEVICE_UA})
    assert r_rot.status_code == 200, f"rotate failed: {r_rot.status_code} {r_rot.text}"
    new_cookie = s1.cookies.get("refresh_token")
    assert new_cookie and new_cookie != old_cookie, "new cookie missing or identical to old"

    # reuse attempt from another session using old cookie -> must be 401
    s2 = requests.Session()
    s2.cookies.set("refresh_token", old_cookie, domain="127.0.0.1", path="/")
    r_reuse = s2.post(f"{BASE}/token/refresh", headers={"User-Agent": "reuse-agent/1.0"})
    assert r_reuse.status_code == 401, f"reuse should be rejected but got {r_reuse.status_code} {r_reuse.text}"

    # small sleep to ensure DB writes finished (sqlite is fast but keep tiny buffer)
    time.sleep(0.05)

    # verify old token row is revoked in DB
    h_old = hashlib.sha256(old_cookie.encode()).hexdigest()
    rows = query_db(
        "SELECT id, user_id, token_hash, device_id, revoked FROM refresh_tokens WHERE token_hash = ?",
        (h_old,),
    )
    assert rows, "old token row not found in DB"
    old_row = rows[0]
    assert old_row[4] == 1 or old_row[4] == True, "old token was not marked revoked"

    # verify new token has device_id preserved (either from user-agent or copied)
    h_new = hashlib.sha256(new_cookie.encode()).hexdigest()
    new_rows = query_db(
        "SELECT id, user_id, token_hash, device_id, revoked FROM refresh_tokens WHERE token_hash = ?",
        (h_new,),
    )
    assert new_rows, "new token row not found in DB"
    new_row = new_rows[0]
    assert new_row[3] is not None, f"new token device_id is empty: {new_row}"

    # verify a reuse_detected event exists for the old token
    evs = query_db(
        "SELECT id, refresh_token_id, user_id, event_type, details FROM refresh_token_events WHERE refresh_token_id = ? ORDER BY created_at DESC LIMIT 5",
        (old_row[0],),
    )
    types = [e[3] for e in evs]
    assert "reuse_detected" in types, f"reuse_detected event not found for token {old_row[0]}, events={evs}"

