import sqlite3
from src.baza import League, Team

conn = sqlite3.connect("nogomet.db")

with conn:
    league = League(conn)
    team = Team(conn)

    # dodamo 1 ligo
    league_id = league.dodaj_vrstico(name="Premier League", season="2024-25")

    # dodamo 1 ekipo v to ligo
    team.dodaj_vrstico(league_id=league_id, name="Liverpool", city="Liverpool", stadium="Anfield", founded_year=1892)

cur = conn.execute("""
    SELECT l.name, l.season, t.name
    FROM league l
    JOIN team t ON t.league_id = l.league_id;
""")
print(cur.fetchall())
conn.close()
