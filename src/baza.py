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
