import sqlite3

conn = sqlite3.connect("nogomet.db")
cur = conn.execute("SELECT team_id, name FROM team;")
print(cur.fetchall())
conn.close()
