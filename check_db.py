import sqlite3

conn = sqlite3.connect("nogomet.db")
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall())
conn.close()
