import csv
from pathlib import Path

parameter_form = ":{}"
base_directory = Path(__file__).resolve().parent.parent
data_directory = base_directory / "data"


class Tabela:
    """Osnovni razred za ustvarjanje tabel in uvoz podatkov iz CSV datotek."""

    ime = None
    pk = None
    podatki = None

    def __init__(self, conn):
        """Shrani povezavo na podatkovno bazo za delo s tabelo."""
        self.conn = conn

    def ustvari(self):
        """Ustvari tabelo v bazi; podrazredi morajo definirati svojo implementacijo."""
        raise NotImplementedError

    def izbrisi_tabelo(self):
        """Izbrise tabelo iz baze, ce tabela obstaja."""
        self.conn.execute(f"DROP TABLE IF EXISTS {self.ime};")

    def uvozi(self, encoding="utf-8"):
        """Uvozi podatke iz pripadajoce CSV datoteke v tabelo."""
        if self.podatki is None:
            return

        pot = data_directory / self.podatki
        if not pot.exists():
            return

        with open(pot, encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row = {k: (None if v == "" else v) for k, v in row.items()}
                self.dodaj_vrstico(**row)

    def dodajanje(self, stolpci):
        """Vrne SQL poizvedbo INSERT za podane stolpce."""
        return f"""
            INSERT INTO {self.ime} ({", ".join(stolpci)})
            VALUES ({", ".join(parameter_form.format(s) for s in stolpci)});
        """

    def dodaj_vrstico(self, **podatki):
        """Doda eno vrstico v tabelo in vrne njen ustvarjeni primarni kljuc."""
        podatki = {k: v for k, v in podatki.items() if v is not None}
        poizvedba = self.dodajanje(podatki.keys())
        cur = self.conn.execute(poizvedba, podatki)
        return cur.lastrowid


class League:
    """Predstavlja eno nogometno ligo in njeno sezono."""

    def __init__(self, league_id, name, season):
        """Ustvari objekt lige s podatki iz tabele league."""
        self.league_id = league_id
        self.name = name
        self.season = season

    @staticmethod
    def poisci_vse(conn):
        """Vrne generator vseh lig iz baze, urejenih po ID-ju."""
        cur = conn.execute("""
            SELECT league_id, name, season
            FROM league
            ORDER BY league_id;
        """)
        for row in cur:
            yield League(*row)

    @staticmethod
    def poisci_po_id(conn, league_id):
        """Vrne ligo z izbranim ID-jem ali None, ce liga ne obstaja."""
        cur = conn.execute("""
            SELECT league_id, name, season
            FROM league
            WHERE league_id = :league_id;
        """, {"league_id": league_id})
        row = cur.fetchone()
        if row is None:
            return None
        return League(*row)

    def vstavi(self, conn):
        """Vstavi ligo v bazo in vrne njen novi ID."""
        cur = conn.execute("""
            INSERT INTO league (name, season)
            VALUES (:name, :season);
        """, {
            "name": self.name,
            "season": self.season,
        })
        self.league_id = cur.lastrowid
        return self.league_id

    def posodobi(self, conn):
        """Posodobi podatke obstojece lige v bazi."""
        conn.execute("""
            UPDATE league
            SET name = :name,
                season = :season
            WHERE league_id = :league_id;
        """, {
            "league_id": self.league_id,
            "name": self.name,
            "season": self.season,
        })

    def izbrisi(self, conn):
        """Izbrise ligo iz baze glede na njen ID."""
        conn.execute("""
            DELETE FROM league
            WHERE league_id = :league_id;
        """, {"league_id": self.league_id})


class Team:
    """Predstavlja eno ekipo oziroma klub v izbrani ligi."""

    def __init__(self, team_id, league_id, name, city, stadium, founded_year):
        """Ustvari objekt ekipe s podatki iz tabele team."""
        self.team_id = team_id
        self.league_id = league_id
        self.name = name
        self.city = city
        self.stadium = stadium
        self.founded_year = founded_year

    @staticmethod
    def poisci_vse(conn):
        """Vrne generator vseh ekip iz baze, urejenih po ID-ju."""
        cur = conn.execute("""
            SELECT team_id, league_id, name, city, stadium, founded_year
            FROM team
            ORDER BY team_id;
        """)
        for row in cur:
            yield Team(*row)

    @staticmethod
    def poisci_po_id(conn, team_id):
        """Vrne ekipo z izbranim ID-jem ali None, ce ekipa ne obstaja."""
        cur = conn.execute("""
            SELECT team_id, league_id, name, city, stadium, founded_year
            FROM team
            WHERE team_id = :team_id;
        """, {"team_id": team_id})
        row = cur.fetchone()
        if row is None:
            return None
        return Team(*row)

    @staticmethod
    def poisci_po_ligi(conn, league_id):
        """Vrne generator vseh ekip v izbrani ligi, urejenih po imenu."""
        cur = conn.execute("""
            SELECT team_id, league_id, name, city, stadium, founded_year
            FROM team
            WHERE league_id = :league_id
            ORDER BY name;
        """, {"league_id": league_id})
        for row in cur:
            yield Team(*row)

    def vstavi(self, conn):
        """Vstavi ekipo v bazo in vrne njen novi ID."""
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
        """Posodobi podatke obstojece ekipe v bazi."""
        conn.execute("""
            UPDATE team
            SET league_id = :league_id,
                name = :name,
                city = :city,
                stadium = :stadium,
                founded_year = :founded_year
            WHERE team_id = :team_id;
        """, {
            "team_id": self.team_id,
            "league_id": self.league_id,
            "name": self.name,
            "city": self.city,
            "stadium": self.stadium,
            "founded_year": self.founded_year,
        })

    def izbrisi(self, conn):
        """Izbrise ekipo iz baze glede na njen ID."""
        conn.execute("""
            DELETE FROM team
            WHERE team_id = :team_id;
        """, {"team_id": self.team_id})


class Player:
    """Predstavlja enega igralca, ki pripada doloceni ekipi."""

    def __init__(self, player_id, team_id, name, age, nationality, position):
        """Ustvari objekt igralca s podatki iz tabele player."""
        self.player_id = player_id
        self.team_id = team_id
        self.name = name
        self.age = age
        self.nationality = nationality
        self.position = position

    @staticmethod
    def poisci_vse(conn):
        """Vrne generator vseh igralcev iz baze, urejenih po ID-ju."""
        cur = conn.execute("""
            SELECT player_id, team_id, name, age, nationality, position
            FROM player
            ORDER BY player_id;
        """)
        for row in cur:
            yield Player(*row)

    @staticmethod
    def poisci_po_id(conn, player_id):
        """Vrne igralca z izbranim ID-jem ali None, ce igralec ne obstaja."""
        cur = conn.execute("""
            SELECT player_id, team_id, name, age, nationality, position
            FROM player
            WHERE player_id = :player_id;
        """, {"player_id": player_id})
        row = cur.fetchone()
        if row is None:
            return None
        return Player(*row)

    @staticmethod
    def poisci_po_ekipi(conn, team_id):
        """Vrne generator vseh igralcev izbrane ekipe, urejenih po imenu."""
        cur = conn.execute("""
            SELECT player_id, team_id, name, age, nationality, position
            FROM player
            WHERE team_id = :team_id
            ORDER BY name;
        """, {"team_id": team_id})
        for row in cur:
            yield Player(*row)

    def vstavi(self, conn):
        """Vstavi igralca v bazo in vrne njegov novi ID."""
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
        """Posodobi podatke obstojecega igralca v bazi."""
        conn.execute("""
            UPDATE player
            SET team_id = :team_id,
                name = :name,
                age = :age,
                nationality = :nationality,
                position = :position
            WHERE player_id = :player_id;
        """, {
            "player_id": self.player_id,
            "team_id": self.team_id,
            "name": self.name,
            "age": self.age,
            "nationality": self.nationality,
            "position": self.position,
        })

    def izbrisi(self, conn):
        """Izbrise igralca iz baze glede na njegov ID."""
        conn.execute("""
            DELETE FROM player
            WHERE player_id = :player_id;
        """, {"player_id": self.player_id})


class Match:
    """Predstavlja eno odigrano tekmo med domaco in gostujoco ekipo."""

    def __init__(self, match_id, league_id, home_team_id, away_team_id, match_date, round_number):
        """Ustvari objekt tekme s podatki iz tabele match."""
        self.match_id = match_id
        self.league_id = league_id
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.match_date = match_date
        self.round_number = round_number

    @staticmethod
    def poisci_vse(conn):
        """Vrne generator vseh tekem iz baze, urejenih po datumu in ID-ju."""
        cur = conn.execute("""
            SELECT match_id, league_id, home_team_id, away_team_id, match_date, round_number
            FROM match
            ORDER BY match_date, match_id;
        """)
        for row in cur:
            yield Match(*row)

    @staticmethod
    def poisci_po_id(conn, match_id):
        """Vrne tekmo z izbranim ID-jem ali None, ce tekma ne obstaja."""
        cur = conn.execute("""
            SELECT match_id, league_id, home_team_id, away_team_id, match_date, round_number
            FROM match
            WHERE match_id = :match_id;
        """, {"match_id": match_id})
        row = cur.fetchone()
        if row is None:
            return None
        return Match(*row)

    @staticmethod
    def poisci_po_ligi(conn, league_id):
        """Vrne generator vseh tekem izbrane lige, urejenih po krogu in datumu."""
        cur = conn.execute("""
            SELECT match_id, league_id, home_team_id, away_team_id, match_date, round_number
            FROM match
            WHERE league_id = :league_id
            ORDER BY round_number, match_date, match_id;
        """, {"league_id": league_id})
        for row in cur:
            yield Match(*row)

    def vstavi(self, conn):
        """Vstavi tekmo v bazo in vrne njen novi ID."""
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
        """Posodobi podatke obstojece tekme v bazi."""
        conn.execute("""
            UPDATE match
            SET league_id = :league_id,
                home_team_id = :home_team_id,
                away_team_id = :away_team_id,
                match_date = :match_date,
                round_number = :round_number
            WHERE match_id = :match_id;
        """, {
            "match_id": self.match_id,
            "league_id": self.league_id,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "match_date": self.match_date,
            "round_number": self.round_number,
        })

    def izbrisi(self, conn):
        """Izbrise tekmo iz baze glede na njen ID."""
        conn.execute("""
            DELETE FROM match
            WHERE match_id = :match_id;
        """, {"match_id": self.match_id})


class MatchStats:
    """Predstavlja statistiko ene tekme, na primer gole, strele in kartone."""

    def __init__(self, match_id, home_goals, away_goals, home_shots, away_shots, home_yellow, away_yellow, home_red, away_red):
        """Ustvari objekt statistike tekme s podatki iz tabele match_stats."""
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
        """Vrne generator vseh statistik tekem, urejenih po ID-ju tekme."""
        cur = conn.execute("""
            SELECT match_id, home_goals, away_goals, home_shots, away_shots,
                   home_yellow, away_yellow, home_red, away_red
            FROM match_stats
            ORDER BY match_id;
        """)
        for row in cur:
            yield MatchStats(*row)

    @staticmethod
    def poisci_po_id(conn, match_id):
        """Vrne statistiko izbrane tekme ali None, ce statistika ne obstaja."""
        cur = conn.execute("""
            SELECT match_id, home_goals, away_goals, home_shots, away_shots,
                   home_yellow, away_yellow, home_red, away_red
            FROM match_stats
            WHERE match_id = :match_id;
        """, {"match_id": match_id})
        row = cur.fetchone()
        if row is None:
            return None
        return MatchStats(*row)

    def vstavi(self, conn):
        """Vstavi statistiko tekme v bazo in vrne ID tekme."""
        conn.execute("""
            INSERT INTO match_stats (
                match_id, home_goals, away_goals, home_shots, away_shots,
                home_yellow, away_yellow, home_red, away_red
            )
            VALUES (
                :match_id, :home_goals, :away_goals, :home_shots, :away_shots,
                :home_yellow, :away_yellow, :home_red, :away_red
            );
        """, self.__dict__)
        return self.match_id

    def posodobi(self, conn):
        """Posodobi statistiko obstojece tekme v bazi."""
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
        """Izbrise statistiko tekme iz baze glede na ID tekme."""
        conn.execute("""
            DELETE FROM match_stats
            WHERE match_id = :match_id;
        """, {"match_id": self.match_id})


class LeagueTabela(Tabela):
    """Opisuje SQL tabelo league in CSV datoteko, iz katere se napolni."""

    ime = "league"
    podatki = "league.csv"

    def ustvari(self):
        """Ustvari tabelo league z ligami in sezonami."""
        self.conn.execute("""
            CREATE TABLE league (
                league_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT NOT NULL,
                season    TEXT NOT NULL,
                UNIQUE(name, season)
            );
        """)


class TeamTabela(Tabela):
    """Opisuje SQL tabelo team in CSV datoteko, iz katere se napolni."""

    ime = "team"
    podatki = "team.csv"

    def ustvari(self):
        """Ustvari tabelo team z ekipami in povezavo na ligo."""
        self.conn.execute("""
            CREATE TABLE team (
                team_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id    INTEGER NOT NULL,
                name         TEXT NOT NULL,
                city         TEXT,
                stadium      TEXT,
                founded_year INTEGER,
                FOREIGN KEY (league_id) REFERENCES league(league_id) ON DELETE CASCADE,
                UNIQUE(league_id, name)
            );
        """)


class PlayerTabela(Tabela):
    """Opisuje SQL tabelo player in CSV datoteko, iz katere se napolni."""

    ime = "player"
    podatki = "player.csv"

    def ustvari(self):
        """Ustvari tabelo player z igralci in povezavo na ekipo."""
        self.conn.execute("""
            CREATE TABLE player (
                player_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id      INTEGER NOT NULL,
                name         TEXT NOT NULL,
                age          INTEGER,
                nationality  TEXT,
                position     TEXT,
                FOREIGN KEY (team_id) REFERENCES team(team_id) ON DELETE CASCADE,
                UNIQUE(team_id, name)
            );
        """)


class MatchTabela(Tabela):
    """Opisuje SQL tabelo match in CSV datoteko, iz katere se napolni."""

    ime = "match"
    podatki = "match.csv"

    def ustvari(self):
        """Ustvari tabelo match s tekmami in povezavami na ligo ter ekipi."""
        self.conn.execute("""
            CREATE TABLE match (
                match_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id     INTEGER NOT NULL,
                home_team_id  INTEGER NOT NULL,
                away_team_id  INTEGER NOT NULL,
                match_date    TEXT NOT NULL,
                round_number  INTEGER,
                FOREIGN KEY (league_id) REFERENCES league(league_id) ON DELETE CASCADE,
                FOREIGN KEY (home_team_id) REFERENCES team(team_id) ON DELETE CASCADE,
                FOREIGN KEY (away_team_id) REFERENCES team(team_id) ON DELETE CASCADE,
                CHECK (home_team_id != away_team_id)
            );
        """)


class MatchStatsTabela(Tabela):
    """Opisuje SQL tabelo match_stats in CSV datoteko, iz katere se napolni."""

    ime = "match_stats"
    podatki = "match_stats.csv"

    def ustvari(self):
        """Ustvari tabelo match_stats s statistiko posamezne tekme."""
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
                FOREIGN KEY (match_id) REFERENCES match(match_id) ON DELETE CASCADE
            );
        """)


class PlayerSeasonStatsTabela(Tabela):
    """Opisuje SQL tabelo player_season_stats in CSV datoteko, iz katere se napolni."""

    ime = "player_season_stats"
    podatki = "player_season_stats.csv"

    def ustvari(self):
        """Ustvari tabelo player_season_stats s sezonsko statistiko igralcev."""
        self.conn.execute("""
            CREATE TABLE player_season_stats (
                player_id      INTEGER PRIMARY KEY,
                matches_played INTEGER DEFAULT 0,
                starts         INTEGER DEFAULT 0,
                minutes_played INTEGER DEFAULT 0,
                goals          INTEGER DEFAULT 0,
                assists        INTEGER DEFAULT 0,
                yellow_cards   INTEGER DEFAULT 0,
                red_cards      INTEGER DEFAULT 0,
                FOREIGN KEY (player_id) REFERENCES player(player_id) ON DELETE CASCADE
            );
        """)


def pripravi_tabele(conn):
    """Vrne seznam objektov tabel v vrstnem redu ustvarjanja in uvoza."""
    return [
        LeagueTabela(conn),
        TeamTabela(conn),
        PlayerTabela(conn),
        MatchTabela(conn),
        MatchStatsTabela(conn),
        PlayerSeasonStatsTabela(conn),
    ]


def ustvari_tabele(tabele):
    """Ustvari vse tabele iz podanega seznama tabel."""
    for tabela in tabele:
        tabela.ustvari()


def izbrisi_tabele(tabele):
    """Izbrise vse tabele v obratnem vrstnem redu zaradi tujih kljucev."""
    for tabela in reversed(tabele):
        tabela.izbrisi_tabelo()


def uvozi_podatke(tabele):
    """Uvozi CSV podatke v vse tabele iz podanega seznama."""
    for tabela in tabele:
        tabela.uvozi()


def ustvari_bazo(conn):
    """Ponovno ustvari celotno bazo in vanjo uvozi zacetne CSV podatke."""
    conn.execute("PRAGMA foreign_keys = ON;")
    tabele = pripravi_tabele(conn)
    izbrisi_tabele(tabele)
    ustvari_tabele(tabele)
    uvozi_podatke(tabele)
