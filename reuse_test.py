# reuse_test.py
import requests, hashlib, sqlite3, json
s1 = requests.Session()
r = s1.post("http://127.0.0.1:8000/token", json={"username":"test@example.com","password":"abc12345"})
print("LOGIN", r.status_code, r.text)
old = s1.cookies.get("refresh_token")
print("OLD_COOKIE (trim):", (old[:20] + "..." + old[-20:]) if old else None)

r1 = s1.post("http://127.0.0.1:8000/token/refresh")
print("ROTATE (session1):", r1.status_code, r1.text)

s2 = requests.Session()
if old:
    s2.cookies.set("refresh_token", old, domain="127.0.0.1", path="/")
r2 = s2.post("http://127.0.0.1:8000/token/refresh")
print("REUSE ATTEMPT (session2):", r2.status_code, r2.text)

if old:
    h = hashlib.sha256(old.encode()).hexdigest()
    c = sqlite3.connect("dev.db")
    rows = c.execute("SELECT id,user_id,token_hash,revoked,created_at,expires_at FROM refresh_tokens WHERE token_hash=?", (h,)).fetchall()
    print("DB rows for old token hash:", json.dumps(rows, default=str))
    evs = c.execute("SELECT id,refresh_token_id,user_id,event_type,ip,user_agent,details,created_at FROM refresh_token_events ORDER BY created_at DESC LIMIT 10").fetchall()
    print("Recent events:", json.dumps(evs, default=str))
    c.close()
