# quick_refresh_test.py
import requests, hashlib, sqlite3, json

BASE = "http://127.0.0.1:8000"
s = requests.Session()

# login
r = s.post(f"{BASE}/token", json={"username": "test@example.com", "password": "abc12345"})
print("LOGIN:", r.status_code, r.text)
old_cookie = s.cookies.get("refresh_token")
print("OLD_COOKIE:", (old_cookie[:40] + "...") if old_cookie else None)

# rotate (session 1)
r_rot = s.post(f"{BASE}/token/refresh")
print("ROTATE:", r_rot.status_code, r_rot.text)
new_cookie = s.cookies.get("refresh_token")
print("NEW_COOKIE:", (new_cookie[:40] + "...") if new_cookie else None)

# reuse attempt from another session using old cookie
s2 = requests.Session()
if old_cookie:
    s2.cookies.set("refresh_token", old_cookie, domain="127.0.0.1", path="/")
r_reuse = s2.post(f"{BASE}/token/refresh")
print("REUSE ATTEMPT:", r_reuse.status_code, r_reuse.text)

# inspect DB for device_id on the new token
h_old = hashlib.sha256(old_cookie.encode()).hexdigest() if old_cookie else None
conn = sqlite3.connect("dev.db")
if h_old:
    rows = conn.execute("SELECT id, user_id, token_hash, device_id, revoked, created_at FROM refresh_tokens WHERE token_hash=?", (h_old,)).fetchall()
    print("DB rows for old token hash:", json.dumps(rows, default=str))
# list last events
events = conn.execute("SELECT id, refresh_token_id, user_id, event_type, ip, user_agent, details, created_at FROM refresh_token_events ORDER BY created_at DESC LIMIT 8").fetchall()
print("Recent events:", json.dumps(events, default=str))
conn.close()
