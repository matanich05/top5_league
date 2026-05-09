import csv
import io
import re
import unicodedata
from pathlib import Path
import zipfile

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

FOOTBALL_DATA_BASE = "https://www.football-data.co.uk/mmz4281/2425"
FBREF_BIG5_PLAYERS = (
    "https://fbref.com/en/comps/Big5/2024-2025/stats/players/"
    "2024-2025-Big-5-European-Leagues-Stats"
)
KAGGLE_PLAYERS_DATASET = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "hubertsidorowicz/football-players-stats-2024-2025"
)

LEAGUES = [
    {
        "name": "Premier League",
        "season": "2024/2025",
        "code": "E0",
        "fbref_comp": "Premier League",
        "matches_per_round": 10,
    },
    {
        "name": "La Liga",
        "season": "2024/2025",
        "code": "SP1",
        "fbref_comp": "La Liga",
        "matches_per_round": 10,
    },
    {
        "name": "Ligue 1",
        "season": "2024/2025",
        "code": "F1",
        "fbref_comp": "Ligue 1",
        "matches_per_round": 9,
    },
    {
        "name": "Bundesliga",
        "season": "2024/2025",
        "code": "D1",
        "fbref_comp": "Bundesliga",
        "matches_per_round": 9,
    },
    {
        "name": "Serie A",
        "season": "2024/2025",
        "code": "I1",
        "fbref_comp": "Serie A",
        "matches_per_round": 10,
    },
]

TEAM_ALIASES = {
    "ath madrid": "atletico madrid",
    "athletic club": "ath bilbao",
    "deportivo alaves": "alaves",
    "celta vigo": "celta",
    "espanyol": "espanol",
    "rayo vallecano": "vallecano",
    "real sociedad": "sociedad",
    "ipswich town": "ipswich",
    "leicester city": "leicester",
    "manchester city": "man city",
    "manchester utd": "man united",
    "newcastle utd": "newcastle",
    "nottingham forest": "nott m forest",
    "nott ham forest": "nott m forest",
    "paris s g": "paris sg",
    "st etienne": "st etienne",
    "saint etienne": "st etienne",
    "eint frankfurt": "ein frankfurt",
    "gladbach": "mgladbach",
    "monchengladbach": "mgladbach",
    "m gladbach": "mgladbach",
    "borussia monchengladbach": "mgladbach",
    "mainz 05": "mainz",
    "koln": "cologne",
    "internazionale": "inter",
    "hellas verona": "verona",
}


def normalize_name(value):
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    text = re.sub(r"\b(fc|cf|afc|sc|ssc|ac|bc)\b", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    return TEAM_ALIASES.get(text, text)


def write_csv(path, fieldnames, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def download_football_data():
    league_rows = []
    team_rows = []
    match_rows = []
    match_stats_rows = []
    team_ids = {}
    match_id = 1

    for league_id, league in enumerate(LEAGUES, start=1):
        league_rows.append({
            "name": league["name"],
            "season": league["season"],
        })

        url = f"{FOOTBALL_DATA_BASE}/{league['code']}.csv"
        df = pd.read_csv(url)
        df = df[df["FTR"].notna()].copy()
        df["parsed_date"] = pd.to_datetime(df["Date"], dayfirst=True)
        df = df.sort_values(["parsed_date", "HomeTeam", "AwayTeam"])

        teams = sorted(set(df["HomeTeam"]).union(df["AwayTeam"]))
        for team in teams:
            team_id = len(team_ids) + 1
            team_ids[(league_id, normalize_name(team))] = team_id
            team_rows.append({
                "league_id": league_id,
                "name": team,
                "city": "",
                "stadium": "",
                "founded_year": "",
            })

        for idx, row in enumerate(df.itertuples(index=False), start=0):
            home_team_id = team_ids[(league_id, normalize_name(row.HomeTeam))]
            away_team_id = team_ids[(league_id, normalize_name(row.AwayTeam))]
            round_number = idx // league["matches_per_round"] + 1

            match_rows.append({
                "league_id": league_id,
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "match_date": row.parsed_date.strftime("%Y-%m-%d"),
                "round_number": round_number,
            })
            match_stats_rows.append({
                "match_id": match_id,
                "home_goals": int(row.FTHG),
                "away_goals": int(row.FTAG),
                "home_shots": int(getattr(row, "HS", 0) or 0),
                "away_shots": int(getattr(row, "AS", 0) or 0),
                "home_yellow": int(getattr(row, "HY", 0) or 0),
                "away_yellow": int(getattr(row, "AY", 0) or 0),
                "home_red": int(getattr(row, "HR", 0) or 0),
                "away_red": int(getattr(row, "AR", 0) or 0),
            })
            match_id += 1

    return league_rows, team_rows, match_rows, match_stats_rows, team_ids


def clean_fbref_columns(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[-1] for col in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]
    df = df[df["Player"].ne("Player")]
    return df


def league_name_from_comp(comp):
    comp = str(comp)
    for league in LEAGUES:
        if league["fbref_comp"] in comp:
            return league["name"]
    return None


def clean_int(value):
    if pd.isna(value) or value == "":
        return 0
    return int(str(value).replace(",", ""))


def age_years(value):
    if pd.isna(value) or value == "":
        return ""
    return str(value).split("-")[0]


def nationality(value):
    if pd.isna(value) or value == "":
        return ""
    parts = str(value).split()
    return parts[-1] if parts else ""


def download_fbref_players(team_ids):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(FBREF_BIG5_PLAYERS, headers=headers, timeout=30)
    response.raise_for_status()

    html = response.text.replace("<!--", "").replace("-->", "")
    tables = pd.read_html(html, attrs={"id": "stats_standard"})
    players = clean_fbref_columns(tables[0])

    league_ids = {league["name"]: idx for idx, league in enumerate(LEAGUES, start=1)}
    player_rows = []
    season_rows = []
    player_id = 1
    missing_teams = []

    for row in players.itertuples(index=False):
        league_name = league_name_from_comp(getattr(row, "Comp"))
        if league_name is None:
            continue

        matches_played = clean_int(getattr(row, "MP"))
        if matches_played == 0:
            continue

        league_id = league_ids[league_name]
        squad = getattr(row, "Squad")
        team_key = (league_id, normalize_name(squad))
        team_id = team_ids.get(team_key)
        if team_id is None:
            missing_teams.append(f"{league_name}: {squad}")
            continue

        player_rows.append({
            "team_id": team_id,
            "name": getattr(row, "Player"),
            "age": age_years(getattr(row, "Age")),
            "nationality": nationality(getattr(row, "Nation")),
            "position": str(getattr(row, "Pos")).split(",")[0],
        })
        season_rows.append({
            "player_id": player_id,
            "matches_played": matches_played,
            "starts": clean_int(getattr(row, "Starts")),
            "minutes_played": clean_int(getattr(row, "Min")),
            "goals": clean_int(getattr(row, "Gls")),
            "assists": clean_int(getattr(row, "Ast")),
            "yellow_cards": clean_int(getattr(row, "CrdY")),
            "red_cards": clean_int(getattr(row, "CrdR")),
        })
        player_id += 1

    if missing_teams:
        unique = sorted(set(missing_teams))
        print("Ekipe iz FBref, ki se niso ujemale z football-data imeni:")
        for item in unique:
            print(f"- {item}")

    return player_rows, season_rows


def download_kaggle_players(team_ids):
    response = requests.get(KAGGLE_PLAYERS_DATASET, timeout=60)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        with zf.open("players_data_light-2024_2025.csv") as f:
            players = pd.read_csv(f)

    league_ids = {league["name"]: idx for idx, league in enumerate(LEAGUES, start=1)}
    player_rows = []
    season_rows = []
    player_id = 1
    missing_teams = []

    for row in players.itertuples(index=False):
        league_name = league_name_from_comp(getattr(row, "Comp"))
        if league_name is None:
            continue

        matches_played = clean_int(getattr(row, "MP"))
        if matches_played == 0:
            continue

        league_id = league_ids[league_name]
        squad = getattr(row, "Squad")
        team_key = (league_id, normalize_name(squad))
        team_id = team_ids.get(team_key)
        if team_id is None:
            missing_teams.append(f"{league_name}: {squad}")
            continue

        player_rows.append({
            "team_id": team_id,
            "name": getattr(row, "Player"),
            "age": age_years(getattr(row, "Age")),
            "nationality": nationality(getattr(row, "Nation")),
            "position": str(getattr(row, "Pos")).split(",")[0],
        })
        season_rows.append({
            "player_id": player_id,
            "matches_played": matches_played,
            "starts": clean_int(getattr(row, "Starts")),
            "minutes_played": clean_int(getattr(row, "Min")),
            "goals": clean_int(getattr(row, "Gls")),
            "assists": clean_int(getattr(row, "Ast")),
            "yellow_cards": clean_int(getattr(row, "CrdY")),
            "red_cards": clean_int(getattr(row, "CrdR")),
        })
        player_id += 1

    if missing_teams:
        unique = sorted(set(missing_teams))
        print("Ekipe iz Kaggle/FBref exporta, ki se niso ujemale z football-data imeni:")
        for item in unique:
            print(f"- {item}")

    return player_rows, season_rows


def main():
    DATA_DIR.mkdir(exist_ok=True)

    league_rows, team_rows, match_rows, match_stats_rows, team_ids = download_football_data()
    try:
        player_rows, season_rows = download_fbref_players(team_ids)
    except requests.HTTPError as exc:
        print(f"FBref neposredni prenos ni uspel ({exc}); uporabljam Kaggle FBref export.")
        player_rows, season_rows = download_kaggle_players(team_ids)

    write_csv(DATA_DIR / "league.csv", ["name", "season"], league_rows)
    write_csv(DATA_DIR / "team.csv", ["league_id", "name", "city", "stadium", "founded_year"], team_rows)
    write_csv(DATA_DIR / "match.csv", [
        "league_id", "home_team_id", "away_team_id", "match_date", "round_number"
    ], match_rows)
    write_csv(DATA_DIR / "match_stats.csv", [
        "match_id", "home_goals", "away_goals", "home_shots", "away_shots",
        "home_yellow", "away_yellow", "home_red", "away_red"
    ], match_stats_rows)
    write_csv(DATA_DIR / "player.csv", [
        "team_id", "name", "age", "nationality", "position"
    ], player_rows)
    write_csv(DATA_DIR / "player_season_stats.csv", [
        "player_id", "matches_played", "starts", "minutes_played",
        "goals", "assists", "yellow_cards", "red_cards"
    ], season_rows)
    print(f"Lige: {len(league_rows)}")
    print(f"Ekipe: {len(team_rows)}")
    print(f"Tekme: {len(match_rows)}")
    print(f"Igralci: {len(player_rows)}")
    print(f"Sezonske statistike igralcev: {len(season_rows)}")
    print("CSV datoteke so posodobljene.")


if __name__ == "__main__":
    main()
