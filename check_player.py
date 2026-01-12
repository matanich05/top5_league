import sqlite3
from src.baza import Player

conn = sqlite3.connect("nogomet.db")
cur = conn.execute("SELECT player_id, team_id, name, age, nationality, position FROM player;")
print(cur.fetchall())

print("---- model (yield) ----")
for p in Player.poisci_vse(conn):
    print(p.player_id, p.name, p.team_id)

conn.close()
