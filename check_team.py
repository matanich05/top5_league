import sqlite3

conn = sqlite3.connect("nogomet.db")
cur = conn.execute("""
    SELECT team_id, league_id, name, city, stadium, founded_year
    FROM team
    ORDER BY team_id;
""")
print(cur.fetchall())
conn.close()