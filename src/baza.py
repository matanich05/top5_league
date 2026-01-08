import sqlite3

PARAM_FMT = ":{}"


class Tabela:
    ime = None

    def __init__(self, conn):
        self.conn = conn

    def ustvari(self):
        raise NotImplementedError

    def izbrisi(self):
        self.conn.execute(f"DROP TABLE IF EXISTS {self.ime};")

    def dodajanje(self, stolpci):
        return f"""
            INSERT INTO {self.ime} ({", ".join(stolpci)})
            VALUES ({", ".join(PARAM_FMT.format(s) for s in stolpci)});
        """

    def dodaj_vrstico(self, **podatki):
        podatki = {k: v for k, v in podatki.items() if v is not None}
        poizvedba = self.dodajanje(podatki.keys())
        cur = self.conn.execute(poizvedba, podatki)
        return cur.lastrowid


class League(Tabela):
    ime = "league"

    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE league (
                league_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT NOT NULL,
                season    TEXT NOT NULL,
                UNIQUE(name, season)
            );
        """)

class Team(Tabela):
    ime = "team"

    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE team (
                team_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id   INTEGER NOT NULL,
                name        TEXT    NOT NULL,
                city        TEXT,
                stadium     TEXT,
                founded_year INTEGER,
                FOREIGN KEY (league_id) REFERENCES league(league_id),
                UNIQUE(league_id, name)
            );
        """)

class Player(Tabela):
    ime = "player"

    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE player (
                player_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id      INTEGER NOT NULL,
                name         TEXT    NOT NULL,
                age          INTEGER,
                nationality  TEXT,
                position     TEXT,
                FOREIGN KEY (team_id) REFERENCES team(team_id),
                UNIQUE(team_id, name)
            );
        """)

class Match(Tabela):
    ime = "match"

    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE match (
                match_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id     INTEGER NOT NULL,
                home_team_id  INTEGER NOT NULL,
                away_team_id  INTEGER NOT NULL,
                match_date    TEXT    NOT NULL,
                round_number  INTEGER,
                FOREIGN KEY (league_id) REFERENCES league(league_id),
                FOREIGN KEY (home_team_id) REFERENCES team(team_id),
                FOREIGN KEY (away_team_id) REFERENCES team(team_id),
                CHECK (home_team_id != away_team_id)
            );
        """)

class MatchStats(Tabela):
    ime = "match_stats"

    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE match_stats (
                match_id     INTEGER PRIMARY KEY,
                home_goals   INTEGER DEFAULT 0,
                away_goals   INTEGER DEFAULT 0,
                home_shots   INTEGER DEFAULT 0,
                away_shots   INTEGER DEFAULT 0,
                home_yellow  INTEGER DEFAULT 0,
                away_yellow  INTEGER DEFAULT 0,
                home_red     INTEGER DEFAULT 0,
                away_red     INTEGER DEFAULT 0,
                FOREIGN KEY (match_id) REFERENCES match(match_id)
            );
        """)

class PlayerMatchStats(Tabela):
    ime = "player_match_stats"

    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE player_match_stats (
                player_id        INTEGER NOT NULL,
                match_id         INTEGER NOT NULL,
                minutes_played   INTEGER DEFAULT 0,
                goals            INTEGER DEFAULT 0,
                assists          INTEGER DEFAULT 0,
                yellow_cards     INTEGER DEFAULT 0,
                red_cards        INTEGER DEFAULT 0,
                rating           REAL,
                PRIMARY KEY (player_id, match_id),
                FOREIGN KEY (player_id) REFERENCES player(player_id),
                FOREIGN KEY (match_id) REFERENCES match(match_id)
            );
        """)



def pripravi_tabele(conn):
    league = League(conn)
    team = Team(conn)
    player = Player(conn)
    match = Match(conn)
    match_stats = MatchStats(conn)
    player_match_stats = PlayerMatchStats(conn)

    return [league, team, player, match, match_stats, player_match_stats]




def ustvari_tabele(tabele):
    for t in tabele:
        t.ustvari()


def izbrisi_tabele(tabele):
    for t in tabele:
        t.izbrisi()


def ustvari_bazo(conn):
    tabele = pripravi_tabele(conn)
    izbrisi_tabele(tabele)
    ustvari_tabele(tabele)
