import sqlite3

c = sqlite3.connect("dev.db")
cur = c.cursor()

print(cur.execute("SELECT sql FROM sqlite_master WHERE name='projects'").fetchone())
print(cur.execute("PRAGMA table_info(projects)").fetchall())
print(cur.execute("SELECT * FROM projects LIMIT 5").fetchall())

c.close()
                                                                                   