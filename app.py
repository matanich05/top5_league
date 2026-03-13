import sqlite3
from flask import Flask, render_template, abort, request

app = Flask(__name__)
DB_PATH = "nogomet.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@app.route("/")
def index():
    conn = get_conn()

    lige = conn.execute("""
        SELECT
            l.league_id,
            l.name,
            l.season,
            COUNT(DISTINCT t.team_id) AS teams_count,
            COUNT(DISTINCT m.match_id) AS matches_count
        FROM league l
        LEFT JOIN team t ON l.league_id = t.league_id
        LEFT JOIN match m ON l.league_id = m.league_id
        GROUP BY l.league_id, l.name, l.season
        ORDER BY l.name;
    """).fetchall()

    zadnje_tekme = conn.execute("""
        SELECT
            m.match_id,
            l.name AS league_name,
            th.name AS home_team,
            ta.name AS away_team,
            m.match_date,
            m.round_number,
            ms.home_goals,
            ms.away_goals
        FROM match m
        JOIN league l ON m.league_id = l.league_id
        JOIN team th ON m.home_team_id = th.team_id
        JOIN team ta ON m.away_team_id = ta.team_id
        LEFT JOIN match_stats ms ON m.match_id = ms.match_id
        ORDER BY m.match_date DESC, m.match_id DESC
        LIMIT 8;
    """).fetchall()

    top_strelci = conn.execute("""
        SELECT
            p.player_id,
            p.name AS player_name,
            t.team_id,
            t.name AS team_name,
            l.league_id,
            l.name AS league_name,
            COALESCE(SUM(pms.goals), 0) AS goals
        FROM player p
        JOIN team t ON p.team_id = t.team_id
        JOIN league l ON t.league_id = l.league_id
        LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
        GROUP BY p.player_id, p.name, t.team_id, t.name, l.league_id, l.name
        ORDER BY goals DESC, p.name ASC
        LIMIT 10;
    """).fetchall()

    top_asistenti = conn.execute("""
        SELECT
            p.player_id,
            p.name AS player_name,
            t.team_id,
            t.name AS team_name,
            l.league_id,
            l.name AS league_name,
            COALESCE(SUM(pms.assists), 0) AS assists
        FROM player p
        JOIN team t ON p.team_id = t.team_id
        JOIN league l ON t.league_id = l.league_id
        LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
        GROUP BY p.player_id, p.name, t.team_id, t.name, l.league_id, l.name
        ORDER BY assists DESC, p.name ASC
        LIMIT 10;
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        lige=lige,
        zadnje_tekme=zadnje_tekme,
        top_strelci=top_strelci,
        top_asistenti=top_asistenti
    )


@app.route("/matches")
def all_matches():
    conn = get_conn()

    league_id = request.args.get("league_id", "").strip()

    lige = conn.execute("""
        SELECT league_id, name, season
        FROM league
        ORDER BY name;
    """).fetchall()

    if league_id.isdigit():
        tekme = conn.execute("""
            SELECT
                m.match_id,
                l.league_id,
                l.name AS league_name,
                l.season,
                th.team_id AS home_team_id,
                th.name AS home_team,
                ta.team_id AS away_team_id,
                ta.name AS away_team,
                m.match_date,
                m.round_number,
                ms.home_goals,
                ms.away_goals
            FROM match m
            JOIN league l ON m.league_id = l.league_id
            JOIN team th ON m.home_team_id = th.team_id
            JOIN team ta ON m.away_team_id = ta.team_id
            LEFT JOIN match_stats ms ON m.match_id = ms.match_id
            WHERE l.league_id = ?
            ORDER BY m.match_date DESC, m.match_id DESC;
        """, (int(league_id),)).fetchall()
    else:
        tekme = conn.execute("""
            SELECT
                m.match_id,
                l.league_id,
                l.name AS league_name,
                l.season,
                th.team_id AS home_team_id,
                th.name AS home_team,
                ta.team_id AS away_team_id,
                ta.name AS away_team,
                m.match_date,
                m.round_number,
                ms.home_goals,
                ms.away_goals
            FROM match m
            JOIN league l ON m.league_id = l.league_id
            JOIN team th ON m.home_team_id = th.team_id
            JOIN team ta ON m.away_team_id = ta.team_id
            LEFT JOIN match_stats ms ON m.match_id = ms.match_id
            ORDER BY m.match_date DESC, m.match_id DESC;
        """).fetchall()

    conn.close()

    return render_template(
        "all_matches.html",
        tekme=tekme,
        lige=lige,
        selected_league_id=league_id
    )


@app.route("/top-scorers")
def top_scorers():
    conn = get_conn()

    league_id = request.args.get("league_id", "").strip()

    lige = conn.execute("""
        SELECT league_id, name, season
        FROM league
        ORDER BY name;
    """).fetchall()

    if league_id.isdigit():
        strelci = conn.execute("""
            SELECT
                p.player_id,
                p.name AS player_name,
                p.position,
                t.team_id,
                t.name AS team_name,
                l.league_id,
                l.name AS league_name,
                COALESCE(COUNT(pms.match_id), 0) AS matches_played,
                COALESCE(SUM(pms.goals), 0) AS goals,
                COALESCE(SUM(pms.assists), 0) AS assists,
                COALESCE(AVG(pms.rating), 0) AS avg_rating
            FROM player p
            JOIN team t ON p.team_id = t.team_id
            JOIN league l ON t.league_id = l.league_id
            LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
            WHERE l.league_id = ?
            GROUP BY
                p.player_id, p.name, p.position,
                t.team_id, t.name,
                l.league_id, l.name
            ORDER BY goals DESC, assists DESC, avg_rating DESC, p.name ASC;
        """, (int(league_id),)).fetchall()
    else:
        strelci = conn.execute("""
            SELECT
                p.player_id,
                p.name AS player_name,
                p.position,
                t.team_id,
                t.name AS team_name,
                l.league_id,
                l.name AS league_name,
                COALESCE(COUNT(pms.match_id), 0) AS matches_played,
                COALESCE(SUM(pms.goals), 0) AS goals,
                COALESCE(SUM(pms.assists), 0) AS assists,
                COALESCE(AVG(pms.rating), 0) AS avg_rating
            FROM player p
            JOIN team t ON p.team_id = t.team_id
            JOIN league l ON t.league_id = l.league_id
            LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
            GROUP BY
                p.player_id, p.name, p.position,
                t.team_id, t.name,
                l.league_id, l.name
            ORDER BY goals DESC, assists DESC, avg_rating DESC, p.name ASC;
        """).fetchall()

    conn.close()

    return render_template(
        "top_scorers.html",
        strelci=strelci,
        lige=lige,
        selected_league_id=league_id
    )


@app.route("/top-assists")
def top_assists():
    conn = get_conn()

    league_id = request.args.get("league_id", "").strip()

    lige = conn.execute("""
        SELECT league_id, name, season
        FROM league
        ORDER BY name;
    """).fetchall()

    if league_id.isdigit():
        asistenti = conn.execute("""
            SELECT
                p.player_id,
                p.name AS player_name,
                p.position,
                t.team_id,
                t.name AS team_name,
                l.league_id,
                l.name AS league_name,
                COALESCE(COUNT(pms.match_id), 0) AS matches_played,
                COALESCE(SUM(pms.goals), 0) AS goals,
                COALESCE(SUM(pms.assists), 0) AS assists,
                COALESCE(AVG(pms.rating), 0) AS avg_rating
            FROM player p
            JOIN team t ON p.team_id = t.team_id
            JOIN league l ON t.league_id = l.league_id
            LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
            WHERE l.league_id = ?
            GROUP BY
                p.player_id, p.name, p.position,
                t.team_id, t.name,
                l.league_id, l.name
            ORDER BY assists DESC, goals DESC, avg_rating DESC, p.name ASC;
        """, (int(league_id),)).fetchall()
    else:
        asistenti = conn.execute("""
            SELECT
                p.player_id,
                p.name AS player_name,
                p.position,
                t.team_id,
                t.name AS team_name,
                l.league_id,
                l.name AS league_name,
                COALESCE(COUNT(pms.match_id), 0) AS matches_played,
                COALESCE(SUM(pms.goals), 0) AS goals,
                COALESCE(SUM(pms.assists), 0) AS assists,
                COALESCE(AVG(pms.rating), 0) AS avg_rating
            FROM player p
            JOIN team t ON p.team_id = t.team_id
            JOIN league l ON t.league_id = l.league_id
            LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
            GROUP BY
                p.player_id, p.name, p.position,
                t.team_id, t.name,
                l.league_id, l.name
            ORDER BY assists DESC, goals DESC, avg_rating DESC, p.name ASC;
        """).fetchall()

    conn.close()

    return render_template(
        "top_assists.html",
        asistenti=asistenti,
        lige=lige,
        selected_league_id=league_id
    )


@app.route("/search")
def search():
    conn = get_conn()

    q = request.args.get("q", "").strip()

    ekipe = []
    igralci = []

    if q:
        ekipe = conn.execute("""
            SELECT
                t.team_id,
                t.name AS team_name,
                t.city,
                l.league_id,
                l.name AS league_name
            FROM team t
            JOIN league l ON t.league_id = l.league_id
            WHERE t.name LIKE ?
               OR t.city LIKE ?
            ORDER BY t.name;
        """, (f"%{q}%", f"%{q}%")).fetchall()

        igralci = conn.execute("""
            SELECT
                p.player_id,
                p.name AS player_name,
                p.position,
                t.team_id,
                t.name AS team_name,
                l.league_id,
                l.name AS league_name
            FROM player p
            JOIN team t ON p.team_id = t.team_id
            JOIN league l ON t.league_id = l.league_id
            WHERE p.name LIKE ?
               OR p.nationality LIKE ?
               OR p.position LIKE ?
            ORDER BY p.name;
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()

    conn.close()

    return render_template(
        "search.html",
        q=q,
        ekipe=ekipe,
        igralci=igralci
    )


@app.route("/league/<int:league_id>")
def league_detail(league_id):
    conn = get_conn()

    selected_round = request.args.get("round", "").strip()

    liga = conn.execute("""
        SELECT league_id, name, season
        FROM league
        WHERE league_id = ?;
    """, (league_id,)).fetchone()

    if liga is None:
        conn.close()
        abort(404)

    ekipe = conn.execute("""
        SELECT team_id, name, city, stadium, founded_year
        FROM team
        WHERE league_id = ?
        ORDER BY name;
    """, (league_id,)).fetchall()

    rounds = conn.execute("""
        SELECT DISTINCT round_number
        FROM match
        WHERE league_id = ?
        ORDER BY round_number;
    """, (league_id,)).fetchall()

    if selected_round.isdigit():
        tekme = conn.execute("""
            SELECT
                m.match_id,
                m.match_date,
                m.round_number,
                th.name AS home_team,
                ta.name AS away_team,
                ms.home_goals,
                ms.away_goals
            FROM match m
            JOIN team th ON m.home_team_id = th.team_id
            JOIN team ta ON m.away_team_id = ta.team_id
            LEFT JOIN match_stats ms ON m.match_id = ms.match_id
            WHERE m.league_id = ? AND m.round_number = ?
            ORDER BY m.round_number, m.match_date;
        """, (league_id, int(selected_round))).fetchall()
    else:
        tekme = conn.execute("""
            SELECT
                m.match_id,
                m.match_date,
                m.round_number,
                th.name AS home_team,
                ta.name AS away_team,
                ms.home_goals,
                ms.away_goals
            FROM match m
            JOIN team th ON m.home_team_id = th.team_id
            JOIN team ta ON m.away_team_id = ta.team_id
            LEFT JOIN match_stats ms ON m.match_id = ms.match_id
            WHERE m.league_id = ?
            ORDER BY m.round_number, m.match_date;
        """, (league_id,)).fetchall()

    lestvica = conn.execute("""
        SELECT
            t.team_id,
            t.name,
            COUNT(ms.match_id) AS played,
            SUM(
                CASE
                    WHEN (m.home_team_id = t.team_id AND ms.home_goals > ms.away_goals)
                      OR (m.away_team_id = t.team_id AND ms.away_goals > ms.home_goals)
                    THEN 1 ELSE 0
                END
            ) AS wins,
            SUM(
                CASE
                    WHEN ms.match_id IS NOT NULL AND ms.home_goals = ms.away_goals
                    THEN 1 ELSE 0
                END
            ) AS draws,
            SUM(
                CASE
                    WHEN (m.home_team_id = t.team_id AND ms.home_goals < ms.away_goals)
                      OR (m.away_team_id = t.team_id AND ms.away_goals < ms.home_goals)
                    THEN 1 ELSE 0
                END
            ) AS losses,
            SUM(
                CASE
                    WHEN ms.match_id IS NULL THEN 0
                    WHEN m.home_team_id = t.team_id THEN ms.home_goals
                    ELSE ms.away_goals
                END
            ) AS goals_for,
            SUM(
                CASE
                    WHEN ms.match_id IS NULL THEN 0
                    WHEN m.home_team_id = t.team_id THEN ms.away_goals
                    ELSE ms.home_goals
                END
            ) AS goals_against,
            SUM(
                CASE
                    WHEN (m.home_team_id = t.team_id AND ms.home_goals > ms.away_goals)
                      OR (m.away_team_id = t.team_id AND ms.away_goals > ms.home_goals)
                    THEN 3
                    WHEN ms.match_id IS NOT NULL AND ms.home_goals = ms.away_goals
                    THEN 1
                    ELSE 0
                END
            ) AS points
        FROM team t
        LEFT JOIN match m
            ON (m.home_team_id = t.team_id OR m.away_team_id = t.team_id)
        LEFT JOIN match_stats ms
            ON m.match_id = ms.match_id
        WHERE t.league_id = ?
        GROUP BY t.team_id
        ORDER BY points DESC, (goals_for - goals_against) DESC, goals_for DESC, t.name ASC;
    """, (league_id,)).fetchall()

    league_top_scorers = conn.execute("""
        SELECT
            p.player_id,
            p.name AS player_name,
            t.team_id,
            t.name AS team_name,
            COALESCE(SUM(pms.goals), 0) AS goals
        FROM player p
        JOIN team t ON p.team_id = t.team_id
        LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
        WHERE t.league_id = ?
        GROUP BY p.player_id, p.name, t.team_id, t.name
        ORDER BY goals DESC, p.name ASC
        LIMIT 5;
    """, (league_id,)).fetchall()

    league_top_assists = conn.execute("""
        SELECT
            p.player_id,
            p.name AS player_name,
            t.team_id,
            t.name AS team_name,
            COALESCE(SUM(pms.assists), 0) AS assists
        FROM player p
        JOIN team t ON p.team_id = t.team_id
        LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
        WHERE t.league_id = ?
        GROUP BY p.player_id, p.name, t.team_id, t.name
        ORDER BY assists DESC, p.name ASC
        LIMIT 5;
    """, (league_id,)).fetchall()

    conn.close()

    return render_template(
        "league_detail.html",
        liga=liga,
        ekipe=ekipe,
        tekme=tekme,
        lestvica=lestvica,
        rounds=rounds,
        selected_round=selected_round,
        league_top_scorers=league_top_scorers,
        league_top_assists=league_top_assists
    )


@app.route("/team/<int:team_id>")
def team_detail(team_id):
    conn = get_conn()

    ekipa = conn.execute("""
        SELECT
            t.team_id,
            t.name,
            t.city,
            t.stadium,
            t.founded_year,
            l.league_id,
            l.name AS league_name,
            l.season
        FROM team t
        JOIN league l ON t.league_id = l.league_id
        WHERE t.team_id = ?;
    """, (team_id,)).fetchone()

    if ekipa is None:
        conn.close()
        abort(404)

    igralci = conn.execute("""
        SELECT player_id, name, age, nationality, position
        FROM player
        WHERE team_id = ?
        ORDER BY name;
    """, (team_id,)).fetchall()

    tekme = conn.execute("""
        SELECT
            m.match_id,
            m.match_date,
            m.round_number,
            th.name AS home_team,
            ta.name AS away_team,
            ms.home_goals,
            ms.away_goals,
            CASE
                WHEN ms.match_id IS NULL THEN '-'
                WHEN (m.home_team_id = ? AND ms.home_goals > ms.away_goals)
                  OR (m.away_team_id = ? AND ms.away_goals > ms.home_goals)
                THEN 'W'
                WHEN ms.home_goals = ms.away_goals
                THEN 'D'
                ELSE 'L'
            END AS result_code
        FROM match m
        JOIN team th ON m.home_team_id = th.team_id
        JOIN team ta ON m.away_team_id = ta.team_id
        LEFT JOIN match_stats ms ON m.match_id = ms.match_id
        WHERE m.home_team_id = ? OR m.away_team_id = ?
        ORDER BY m.match_date DESC, m.match_id DESC;
    """, (team_id, team_id, team_id, team_id)).fetchall()

    team_stats = conn.execute("""
        SELECT
            COUNT(ms.match_id) AS played,
            SUM(
                CASE
                    WHEN (m.home_team_id = ? AND ms.home_goals > ms.away_goals)
                      OR (m.away_team_id = ? AND ms.away_goals > ms.home_goals)
                    THEN 1 ELSE 0
                END
            ) AS wins,
            SUM(
                CASE
                    WHEN ms.match_id IS NOT NULL AND ms.home_goals = ms.away_goals
                    THEN 1 ELSE 0
                END
            ) AS draws,
            SUM(
                CASE
                    WHEN (m.home_team_id = ? AND ms.home_goals < ms.away_goals)
                      OR (m.away_team_id = ? AND ms.away_goals < ms.home_goals)
                    THEN 1 ELSE 0
                END
            ) AS losses,
            SUM(
                CASE
                    WHEN ms.match_id IS NULL THEN 0
                    WHEN m.home_team_id = ? THEN ms.home_goals
                    ELSE ms.away_goals
                END
            ) AS goals_for,
            SUM(
                CASE
                    WHEN ms.match_id IS NULL THEN 0
                    WHEN m.home_team_id = ? THEN ms.away_goals
                    ELSE ms.home_goals
                END
            ) AS goals_against,
            SUM(
                CASE
                    WHEN (m.home_team_id = ? AND ms.home_goals > ms.away_goals)
                      OR (m.away_team_id = ? AND ms.away_goals > ms.home_goals)
                    THEN 3
                    WHEN ms.match_id IS NOT NULL AND ms.home_goals = ms.away_goals
                    THEN 1
                    ELSE 0
                END
            ) AS points
        FROM match m
        LEFT JOIN match_stats ms ON m.match_id = ms.match_id
        WHERE m.home_team_id = ? OR m.away_team_id = ?;
    """, (
        team_id, team_id,
        team_id, team_id,
        team_id, team_id,
        team_id, team_id,
        team_id, team_id
    )).fetchone()

    top_scorer = conn.execute("""
        SELECT
            p.player_id,
            p.name AS player_name,
            COALESCE(SUM(pms.goals), 0) AS goals
        FROM player p
        LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
        WHERE p.team_id = ?
        GROUP BY p.player_id, p.name
        ORDER BY goals DESC, p.name ASC
        LIMIT 1;
    """, (team_id,)).fetchone()

    top_assistant = conn.execute("""
        SELECT
            p.player_id,
            p.name AS player_name,
            COALESCE(SUM(pms.assists), 0) AS assists
        FROM player p
        LEFT JOIN player_match_stats pms ON p.player_id = pms.player_id
        WHERE p.team_id = ?
        GROUP BY p.player_id, p.name
        ORDER BY assists DESC, p.name ASC
        LIMIT 1;
    """, (team_id,)).fetchone()

    form = conn.execute("""
        SELECT
            CASE
                WHEN ms.match_id IS NULL THEN '-'
                WHEN (m.home_team_id = ? AND ms.home_goals > ms.away_goals)
                  OR (m.away_team_id = ? AND ms.away_goals > ms.home_goals)
                THEN 'W'
                WHEN ms.home_goals = ms.away_goals
                THEN 'D'
                ELSE 'L'
            END AS result_code
        FROM match m
        LEFT JOIN match_stats ms ON m.match_id = ms.match_id
        WHERE m.home_team_id = ? OR m.away_team_id = ?
        ORDER BY m.match_date DESC, m.match_id DESC
        LIMIT 5;
    """, (team_id, team_id, team_id, team_id)).fetchall()

    conn.close()

    return render_template(
        "team_detail.html",
        ekipa=ekipa,
        igralci=igralci,
        tekme=tekme,
        team_stats=team_stats,
        top_scorer=top_scorer,
        top_assistant=top_assistant,
        form=form
    )


@app.route("/match/<int:match_id>")
def match_detail(match_id):
    conn = get_conn()

    tekma = conn.execute("""
        SELECT
            m.match_id,
            m.match_date,
            m.round_number,
            l.league_id,
            l.name AS league_name,
            l.season,
            th.team_id AS home_team_id,
            th.name AS home_team,
            ta.team_id AS away_team_id,
            ta.name AS away_team,
            ms.home_goals,
            ms.away_goals,
            ms.home_shots,
            ms.away_shots,
            ms.home_yellow,
            ms.away_yellow,
            ms.home_red,
            ms.away_red
        FROM match m
        JOIN league l ON m.league_id = l.league_id
        JOIN team th ON m.home_team_id = th.team_id
        JOIN team ta ON m.away_team_id = ta.team_id
        LEFT JOIN match_stats ms ON m.match_id = ms.match_id
        WHERE m.match_id = ?;
    """, (match_id,)).fetchone()

    if tekma is None:
        conn.close()
        abort(404)

    home_players = conn.execute("""
        SELECT
            p.player_id,
            p.name AS player_name,
            p.position,
            COALESCE(pms.minutes_played, 0) AS minutes_played,
            COALESCE(pms.goals, 0) AS goals,
            COALESCE(pms.assists, 0) AS assists,
            COALESCE(pms.yellow_cards, 0) AS yellow_cards,
            COALESCE(pms.red_cards, 0) AS red_cards,
            pms.rating
        FROM player p
        LEFT JOIN player_match_stats pms
            ON p.player_id = pms.player_id AND pms.match_id = ?
        WHERE p.team_id = ?
        ORDER BY p.name;
    """, (match_id, tekma["home_team_id"])).fetchall()

    away_players = conn.execute("""
        SELECT
            p.player_id,
            p.name AS player_name,
            p.position,
            COALESCE(pms.minutes_played, 0) AS minutes_played,
            COALESCE(pms.goals, 0) AS goals,
            COALESCE(pms.assists, 0) AS assists,
            COALESCE(pms.yellow_cards, 0) AS yellow_cards,
            COALESCE(pms.red_cards, 0) AS red_cards,
            pms.rating
        FROM player p
        LEFT JOIN player_match_stats pms
            ON p.player_id = pms.player_id AND pms.match_id = ?
        WHERE p.team_id = ?
        ORDER BY p.name;
    """, (match_id, tekma["away_team_id"])).fetchall()

    conn.close()

    return render_template(
        "match_detail.html",
        tekma=tekma,
        home_players=home_players,
        away_players=away_players
    )


@app.route("/player/<int:player_id>")
def player_detail(player_id):
    conn = get_conn()

    igralec = conn.execute("""
        SELECT
            p.player_id,
            p.name,
            p.age,
            p.nationality,
            p.position,
            t.team_id,
            t.name AS team_name,
            l.league_id,
            l.name AS league_name,
            l.season
        FROM player p
        JOIN team t ON p.team_id = t.team_id
        JOIN league l ON t.league_id = l.league_id
        WHERE p.player_id = ?;
    """, (player_id,)).fetchone()

    if igralec is None:
        conn.close()
        abort(404)

    statistika = conn.execute("""
        SELECT
            COUNT(*) AS matches_played,
            COALESCE(SUM(goals), 0) AS total_goals,
            COALESCE(SUM(assists), 0) AS total_assists,
            COALESCE(SUM(yellow_cards), 0) AS total_yellow,
            COALESCE(SUM(red_cards), 0) AS total_red,
            COALESCE(AVG(rating), 0) AS avg_rating
        FROM player_match_stats
        WHERE player_id = ?;
    """, (player_id,)).fetchone()

    conn.close()

    return render_template(
        "player_detail.html",
        igralec=igralec,
        statistika=statistika
    )


if __name__ == "__main__":
    app.run(debug=True)