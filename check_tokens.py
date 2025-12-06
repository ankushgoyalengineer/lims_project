# check_tokens.py
import sqlite3
import json

c = sqlite3.connect("dev.db")
cur = c.cursor()
cur.execute(
    "SELECT id, user_id, revoked, created_at, expires_at "
    "FROM refresh_tokens WHERE revoked=0 ORDER BY created_at DESC"
)
rows = cur.fetchall()
print(json.dumps(rows, default=str, indent=2))
c.close()
