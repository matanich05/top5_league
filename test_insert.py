import sqlite3
from src.baza import League, Team

conn = sqlite3.connect("nogomet.db")
conn.execute("PRAGMA foreign_keys = ON;")

with conn:
    liga = League(None, "Premier League", "2024/2025")
    league_id = liga.vstavi(conn)

    ekipa = Team(None, league_id, "Liverpool", "Liverpool", "Anfield", 1892)
    ekipa.vstavi(conn)

cur = conn.execute("""
    SELECT l.name, l.season, t.name
    FROM league l
    JOIN team t ON t.league_id = l.league_id
    ORDER BY l.league_id, t.team_id;
""")

print(cur.fetchall())
conn.close()