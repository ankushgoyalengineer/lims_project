# scripts/cleanup_refresh_tokens.py
import sqlite3
from datetime import datetime, timedelta

DB = "dev.db"

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    now = datetime.utcnow()
    # revoke cleanup: remove revoked tokens older than 30 days
    cutoff_revoked = (now - timedelta(days=30)).isoformat()
    cur.execute(
        "DELETE FROM refresh_tokens WHERE revoked=1 AND created_at < ?",
        (cutoff_revoked,),
    )

    # expired tokens: remove tokens that expired over 7 days ago
    cutoff_expired = (now - timedelta(days=7)).isoformat()
    cur.execute(
        "DELETE FROM refresh_tokens WHERE expires_at IS NOT NULL AND expires_at < ?",
        (cutoff_expired,),
    )

    conn.commit()
    conn.close()
    print("cleanup done")

if __name__ == '__main__':
    main()
