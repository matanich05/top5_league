import sqlite3

conn = sqlite3.connect("nogomet.db")
cur = conn.execute("""
    SELECT league_id, name, season
    FROM league
    ORDER BY league_id;
""")
print(cur.fetchall())
conn.close()