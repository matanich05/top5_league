import csv

PARAM_FMT = ":{}"


class Tabela:
    ime = None
    pk = None
    podatki = None

    def __init__(self, conn):
        self.conn = conn

    def ustvari(self):
        raise NotImplementedError

    def izbrisi_tabelo(self):
        self.conn.execute(f"DROP TABLE IF EXISTS {self.ime};")

    def uvozi(self, encoding="utf-8"):
        if self.podatki is None:
            return
        with open(self.podatki, encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row = {k: (None if v == "" else v) for k, v in row.items()}
                self.dodaj_vrstico(**row)

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


# -------------------------
# MODEL: entitete (vrstice)
# -------------------------

class League:
    def __init__(self, league_id, name, season):
        self.league_id = league_id
        self.name = name
        self.season = season

    @staticmethod
    def poisci_vse(conn):
        cur = conn.execute("SELECT league_id, name, season FROM league ORDER BY league_id;")
        for league_id, name, season in cur:
            yield League(league_id, name, season)

    @staticmethod
    def poisci_po_id(conn, league_id):
        cur = conn.execute(
            "SELECT league_id, name, season FROM league WHERE league_id = :league_id;",
            {"league_id": league_id},
        )
        r = cur.fetchone()
        if r is None:
            return None
        return League(*r)

    def vstavi(self, conn):
        cur = conn.execute(
            "INSERT INTO league (name, season) VALUES (:name, :season);",
            {"name": self.name, "season": self.season},
        )
        self.league_id = cur.lastrowid
        return self.league_id

    def posodobi(self, conn):
        conn.execute(
            "UPDATE league SET name = :name, season = :season WHERE league_id = :league_id;",
            {"name": self.name, "season": self.season, "league_id": self.league_id},
        )

    def izbrisi(self, conn):
        conn.execute(
            "DELETE FROM league WHERE league_id = :league_id;",
            {"league_id": self.league_id},
        )


class Team:
    def __init__(self, team_id, league_id, name, city, stadium, founded_year):
        self.team_id = team_id
        self.league_id = league_id
        self.name = name
        self.city = city
        self.stadium = stadium
        self.founded_year = founded_year

    @staticmethod
    def poisci_vse(conn):
        cur = conn.execute("""
            SELECT team_id, league_id, name, city, stadium, founded_year
            FROM team
            ORDER BY team_id;
        """)
        for row in cur:
            yield Team(*row)

    @staticmethod
    def poisci_po_id(conn, team_id):
        cur = conn.execute("""
            SELECT team_id, league_id, name, city, stadium, founded_year
            FROM team
            WHERE team_id = :team_id;
        """, {"team_id": team_id})
        r = cur.fetchone()
        if r is None:
            return None
        return Team(*r)

    def vstavi(self, conn):
        cur = conn.execute("""
            INSERT INTO team (league_id, name, city, stadium, founded_year)
            VALUES (:league_id, :name, :city, :stadium, :founded_year);
        """, {
            "league_id": self.league_id,
            "name": self.name,
            "city": self.city,
            "stadium": self.stadium,
            "founded_year": self.founded_year,
        })
        self.team_id = cur.lastrowid
        return self.team_id

    def posodobi(self, conn):
        conn.execute("""
            UPDATE team
            SET league_id = :league_id,
                name = :name,
                city = :city,
                stadium = :stadium,
                founded_year = :founded_year
            WHERE team_id = :team_id;
        """, {
            "league_id": self.league_id,
            "name": self.name,
            "city": self.city,
            "stadium": self.stadium,
            "founded_year": self.founded_year,
            "team_id": self.team_id,
        })

    def izbrisi(self, conn):
        conn.execute("DELETE FROM team WHERE team_id = :team_id;", {"team_id": self.team_id})


class Player:
    def __init__(self, player_id, team_id, name, age, nationality, position):
        self.player_id = player_id
        self.team_id = team_id
        self.name = name
        self.age = age
        self.nationality = nationality
        self.position = position

    @staticmethod
    def poisci_vse(conn):
        cur = conn.execute("""
            SELECT player_id, team_id, name, age, nationality, position
            FROM player
            ORDER BY player_id;
        """)
        for row in cur:
            yield Player(*row)

    @staticmethod
    def poisci_po_id(conn, player_id):
        cur = conn.execute("""
            SELECT player_id, team_id, name, age, nationality, position
            FROM player
            WHERE player_id = :player_id;
        """, {"player_id": player_id})
        r = cur.fetchone()
        if r is None:
            return None
        return Player(*r)

    def vstavi(self, conn):
        cur = conn.execute("""
            INSERT INTO player (team_id, name, age, nationality, position)
            VALUES (:team_id, :name, :age, :nationality, :position);
        """, {
            "team_id": self.team_id,
            "name": self.name,
            "age": self.age,
            "nationality": self.nationality,
            "position": self.position,
        })
        self.player_id = cur.lastrowid
        return self.player_id

    def posodobi(self, conn):
        conn.execute("""
            UPDATE player
            SET team_id = :team_id,
                name = :name,
                age = :age,
                nationality = :nationality,
                position = :position
            WHERE player_id = :player_id;
        """, {
            "team_id": self.team_id,
            "name": self.name,
            "age": self.age,
            "nationality": self.nationality,
            "position": self.position,
            "player_id": self.player_id,
        })

    def izbrisi(self, conn):
        conn.execute("DELETE FROM player WHERE player_id = :player_id;", {"player_id": self.player_id})


class Match:
    def __init__(self, match_id, league_id, home_team_id, away_team_id, match_date, round_number):
        self.match_id = match_id
        self.league_id = league_id
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.match_date = match_date
        self.round_number = round_number

    @staticmethod
    def poisci_vse(conn):
        cur = conn.execute("""
            SELECT match_id, league_id, home_team_id, away_team_id, match_date, round_number
            FROM match
            ORDER BY match_id;
        """)
        for row in cur:
            yield Match(*row)

    @staticmethod
    def poisci_po_id(conn, match_id):
        cur = conn.execute("""
            SELECT match_id, league_id, home_team_id, away_team_id, match_date, round_number
            FROM match
            WHERE match_id = :match_id;
        """, {"match_id": match_id})
        r = cur.fetchone()
        if r is None:
            return None
        return Match(*r)

    def vstavi(self, conn):
        cur = conn.execute("""
            INSERT INTO match (league_id, home_team_id, away_team_id, match_date, round_number)
            VALUES (:league_id, :home_team_id, :away_team_id, :match_date, :round_number);
        """, {
            "league_id": self.league_id,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "match_date": self.match_date,
            "round_number": self.round_number,
        })
        self.match_id = cur.lastrowid
        return self.match_id

    def posodobi(self, conn):
        conn.execute("""
            UPDATE match
            SET league_id = :league_id,
                home_team_id = :home_team_id,
                away_team_id = :away_team_id,
                match_date = :match_date,
                round_number = :round_number
            WHERE match_id = :match_id;
        """, {
            "league_id": self.league_id,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "match_date": self.match_date,
            "round_number": self.round_number,
            "match_id": self.match_id,
        })

    def izbrisi(self, conn):
        conn.execute("DELETE FROM match WHERE match_id = :match_id;", {"match_id": self.match_id})


class MatchStats:
    def __init__(self, match_id, home_goals, away_goals, home_shots, away_shots, home_yellow, away_yellow, home_red, away_red):
        self.match_id = match_id
        self.home_goals = home_goals
        self.away_goals = away_goals
        self.home_shots = home_shots
        self.away_shots = away_shots
        self.home_yellow = home_yellow
        self.away_yellow = away_yellow
        self.home_red = home_red
        self.away_red = away_red

    @staticmethod
    def poisci_vse(conn):
        cur = conn.execute("""
            SELECT match_id, home_goals, away_goals, home_shots, away_shots, home_yellow, away_yellow, home_red, away_red
            FROM match_stats
            ORDER BY match_id;
        """)
        for row in cur:
            yield MatchStats(*row)

    @staticmethod
    def poisci_po_id(conn, match_id):
        cur = conn.execute("""
            SELECT match_id, home_goals, away_goals, home_shots, away_shots, home_yellow, away_yellow, home_red, away_red
            FROM match_stats
            WHERE match_id = :match_id;
        """, {"match_id": match_id})
        r = cur.fetchone()
        if r is None:
            return None
        return MatchStats(*r)

    def vstavi(self, conn):
        conn.execute("""
            INSERT INTO match_stats (match_id, home_goals, away_goals, home_shots, away_shots, home_yellow, away_yellow, home_red, away_red)
            VALUES (:match_id, :home_goals, :away_goals, :home_shots, :away_shots, :home_yellow, :away_yellow, :home_red, :away_red);
        """, self.__dict__)
        return self.match_id

    def posodobi(self, conn):
        conn.execute("""
            UPDATE match_stats
            SET home_goals = :home_goals,
                away_goals = :away_goals,
                home_shots = :home_shots,
                away_shots = :away_shots,
                home_yellow = :home_yellow,
                away_yellow = :away_yellow,
                home_red = :home_red,
                away_red = :away_red
            WHERE match_id = :match_id;
        """, self.__dict__)

    def izbrisi(self, conn):
        conn.execute("DELETE FROM match_stats WHERE match_id = :match_id;", {"match_id": self.match_id})


class PlayerMatchStats:
    def __init__(self, player_id, match_id, minutes_played, goals, assists, yellow_cards, red_cards, rating):
        self.player_id = player_id
        self.match_id = match_id
        self.minutes_played = minutes_played
        self.goals = goals
        self.assists = assists
        self.yellow_cards = yellow_cards
        self.red_cards = red_cards
        self.rating = rating

    @staticmethod
    def poisci_vse(conn):
        cur = conn.execute("""
            SELECT player_id, match_id, minutes_played, goals, assists, yellow_cards, red_cards, rating
            FROM player_match_stats
            ORDER BY player_id, match_id;
        """)
        for row in cur:
            yield PlayerMatchStats(*row)

    @staticmethod
    def poisci_po_id(conn, player_id, match_id):
        cur = conn.execute("""
            SELECT player_id, match_id, minutes_played, goals, assists, yellow_cards, red_cards, rating
            FROM player_match_stats
            WHERE player_id = :player_id AND match_id = :match_id;
        """, {"player_id": player_id, "match_id": match_id})
        r = cur.fetchone()
        if r is None:
            return None
        return PlayerMatchStats(*r)

    def vstavi(self, conn):
        conn.execute("""
            INSERT INTO player_match_stats (player_id, match_id, minutes_played, goals, assists, yellow_cards, red_cards, rating)
            VALUES (:player_id, :match_id, :minutes_played, :goals, :assists, :yellow_cards, :red_cards, :rating);
        """, self.__dict__)
        return (self.player_id, self.match_id)

    def posodobi(self, conn):
        conn.execute("""
            UPDATE player_match_stats
            SET minutes_played = :minutes_played,
                goals = :goals,
                assists = :assists,
                yellow_cards = :yellow_cards,
                red_cards = :red_cards,
                rating = :rating
            WHERE player_id = :player_id AND match_id = :match_id;
        """, self.__dict__)

    def izbrisi(self, conn):
        conn.execute("""
            DELETE FROM player_match_stats
            WHERE player_id = :player_id AND match_id = :match_id;
        """, {"player_id": self.player_id, "match_id": self.match_id})


# -------------------------
# BAZA: ustvarjanje + uvoz
# -------------------------

class LeagueTabela(Tabela):
    ime = "league"
    podatki = "data/league.csv"

    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE league (
                league_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT NOT NULL,
                season    TEXT NOT NULL,
                UNIQUE(name, season)
            );
        """)


class TeamTabela(Tabela):
    ime = "team"
    podatki = "data/team.csv"

    def ustvari(self):
        self.conn.execute("""
            CREATE TABLE team (
                team_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id    INTEGER NOT NULL,
                name         TEXT    NOT NULL,
                city         TEXT,
                stadium      TEXT,
                founded_year INTEGER,
                FOREIGN KEY (league_id) REFERENCES league(league_id),
                UNIQUE(league_id, name)
            );
        """)


class PlayerTabela(Tabela):
    ime = "player"
    podatki = "data/player.csv"

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


class MatchTabela(Tabela):
    ime = "match"
    podatki = "data/match.csv"

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


class MatchStatsTabela(Tabela):
    ime = "match_stats"
    podatki = "data/match_stats.csv"

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


class PlayerMatchStatsTabela(Tabela):
    ime = "player_match_stats"
    podatki = "data/player_match_stats.csv"

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
    return [
        LeagueTabela(conn),
        TeamTabela(conn),
        PlayerTabela(conn),
        MatchTabela(conn),
        MatchStatsTabela(conn),
        PlayerMatchStatsTabela(conn),
    ]


def ustvari_tabele(tabele):
    for t in tabele:
        t.ustvari()


def izbrisi_tabele(tabele):
    for t in tabele:
        t.izbrisi_tabelo()


def uvozi_podatke(tabele):
    for t in tabele:
        t.uvozi()


def ustvari_bazo(conn):
    tabele = pripravi_tabele(conn)
    izbrisi_tabele(tabele)
    ustvari_tabele(tabele)
    uvozi_podatke(tabele)
