import sqlite3

c = sqlite3.connect("dev.db")

c.execute("""
CREATE TABLE IF NOT EXISTS refresh_token_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    refresh_token_id INTEGER,
    user_id INTEGER,
    event_type VARCHAR(32) NOT NULL,
    ip VARCHAR(64),
    user_agent VARCHAR(256),
    details TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
""")

c.execute("""
CREATE INDEX IF NOT EXISTS ix_refresh_token_events_refresh_token_id 
ON refresh_token_events(refresh_token_id);
""")

c.execute("""
CREATE INDEX IF NOT EXISTS ix_refresh_token_events_user_id 
ON refresh_token_events(user_id);
""")

c.commit()
c.close()

print("done")
