import sqlite3
from src.baza import League, Team, Player


def izpisi_lige(conn):
    print("\n--- LIGE ---")
    najdeno = False
    for liga in League.poisci_vse(conn):
        najdeno = True
        print(f"{liga.league_id}: {liga.name} ({liga.season})")
    if not najdeno:
        print("Ni lig.")


def izpisi_ekipe(conn):
    print("\n--- EKIPE ---")
    najdeno = False
    for ekipa in Team.poisci_vse(conn):
        najdeno = True
        print(
            f"{ekipa.team_id}: {ekipa.name}, "
            f"liga {ekipa.league_id}, "
            f"mesto {ekipa.city}, "
            f"stadion {ekipa.stadium}"
        )
    if not najdeno:
        print("Ni ekip.")


def izpisi_ekipe_po_ligi(conn):
    print("\n--- EKIPE PO LIGI ---")
    league_id = input("Vnesi ID lige: ")

    if not league_id.isdigit():
        print("ID lige mora biti število.")
        return

    liga = League.poisci_po_id(conn, int(league_id))
    if liga is None:
        print("Liga ne obstaja.")
        return

    print(f"\nEkipe v ligi {liga.name} ({liga.season}):")
    najdeno = False
    for ekipa in Team.poisci_po_ligi(conn, int(league_id)):
        najdeno = True
        print(f"{ekipa.team_id}: {ekipa.name} - {ekipa.city}")
    if not najdeno:
        print("Ta liga nima ekip.")


def izpisi_igralce(conn):
    print("\n--- IGRALCI ---")
    najdeno = False
    for igralec in Player.poisci_vse(conn):
        najdeno = True
        print(
            f"{igralec.player_id}: {igralec.name}, "
            f"ekipa {igralec.team_id}, "
            f"starost {igralec.age}, "
            f"narodnost {igralec.nationality}, "
            f"pozicija {igralec.position}"
        )
    if not najdeno:
        print("Ni igralcev.")


def izpisi_igralce_po_ekipi(conn):
    print("\n--- IGRALCI PO EKIPI ---")
    team_id = input("Vnesi ID ekipe: ")

    if not team_id.isdigit():
        print("ID ekipe mora biti število.")
        return

    ekipa = Team.poisci_po_id(conn, int(team_id))
    if ekipa is None:
        print("Ekipa ne obstaja.")
        return

    print(f"\nIgralci ekipe {ekipa.name}:")
    najdeno = False
    for igralec in Player.poisci_po_ekipi(conn, int(team_id)):
        najdeno = True
        print(
            f"{igralec.player_id}: {igralec.name}, "
            f"{igralec.position}, "
            f"starost {igralec.age}, "
            f"{igralec.nationality}"
        )
    if not najdeno:
        print("Ta ekipa nima igralcev.")


def izpisi_tekme(conn):
    print("\n--- TEKME ---")
    cur = conn.execute("""
        SELECT m.match_id, l.name, th.name, ta.name, m.match_date, m.round_number
        FROM match m
        JOIN league l ON m.league_id = l.league_id
        JOIN team th ON m.home_team_id = th.team_id
        JOIN team ta ON m.away_team_id = ta.team_id
        ORDER BY m.match_date, m.match_id;
    """)
    rows = cur.fetchall()

    if not rows:
        print("Ni tekem.")
        return

    for match_id, league_name, home_team, away_team, match_date, round_number in rows:
        print(
            f"{match_id}: {league_name} | "
            f"{home_team} vs {away_team} | "
            f"datum {match_date} | "
            f"krog {round_number}"
        )


def izpisi_tekme_po_ligi(conn):
    print("\n--- TEKME PO LIGI ---")
    league_id = input("Vnesi ID lige: ")

    if not league_id.isdigit():
        print("ID lige mora biti število.")
        return

    liga = League.poisci_po_id(conn, int(league_id))
    if liga is None:
        print("Liga ne obstaja.")
        return

    cur = conn.execute("""
        SELECT m.match_id, th.name, ta.name, m.match_date, m.round_number
        FROM match m
        JOIN team th ON m.home_team_id = th.team_id
        JOIN team ta ON m.away_team_id = ta.team_id
        WHERE m.league_id = :league_id
        ORDER BY m.round_number, m.match_date, m.match_id;
    """, {"league_id": int(league_id)})
    rows = cur.fetchall()

    print(f"\nTekme v ligi {liga.name} ({liga.season}):")
    if not rows:
        print("Ta liga nima tekem.")
        return

    for match_id, home_team, away_team, match_date, round_number in rows:
        print(
            f"{match_id}: {home_team} vs {away_team} | "
            f"datum {match_date} | "
            f"krog {round_number}"
        )


def izpisi_lestvico_lige(conn):
    print("\n--- LESTVICA LIGE ---")
    league_id = input("Vnesi ID lige: ").strip()

    if not league_id.isdigit():
        print("ID lige mora biti število.")
        return

    liga = League.poisci_po_id(conn, int(league_id))
    if liga is None:
        print("Liga ne obstaja.")
        return

    rows = conn.execute("""
        SELECT
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
    """, (int(league_id),)).fetchall()

    print(f"\nLestvica: {liga.name} ({liga.season})")
    print(f"{'#':>2}  {'Ekipa':<24} {'OD':>3} {'Z':>3} {'R':>3} {'P':>3} {'Goli':>9} {'T':>3}")
    for i, row in enumerate(rows, start=1):
        name, played, wins, draws, losses, goals_for, goals_against, points = row
        print(
            f"{i:>2}  {name:<24} {played or 0:>3} {wins or 0:>3} "
            f"{draws or 0:>3} {losses or 0:>3} "
            f"{goals_for or 0:>3}:{goals_against or 0:<3} {points or 0:>3}"
        )


def izpisi_top_strelce(conn):
    print("\n--- TOP STRELCI ---")
    limit = input("Koliko igralcev naj prikažem? [10]: ").strip()
    limit = int(limit) if limit.isdigit() else 10

    rows = conn.execute("""
        SELECT
            p.name,
            t.name,
            l.name,
            COALESCE(pss.matches_played, 0),
            COALESCE(pss.goals, 0),
            COALESCE(pss.assists, 0)
        FROM player p
        JOIN team t ON p.team_id = t.team_id
        JOIN league l ON t.league_id = l.league_id
        LEFT JOIN player_season_stats pss ON p.player_id = pss.player_id
        ORDER BY pss.goals DESC, pss.assists DESC, p.name ASC
        LIMIT ?;
    """, (limit,)).fetchall()

    print(f"{'#':>2}  {'Igralec':<24} {'Ekipa':<18} {'Liga':<16} {'Tekme':>5} {'G':>3} {'A':>3}")
    for i, (player, team, league, matches, goals, assists) in enumerate(rows, start=1):
        print(f"{i:>2}  {player:<24} {team:<18} {league:<16} {matches:>5} {goals:>3} {assists:>3}")


def izpisi_top_asistente(conn):
    print("\n--- TOP ASISTENTI ---")
    limit = input("Koliko igralcev naj prikažem? [10]: ").strip()
    limit = int(limit) if limit.isdigit() else 10

    rows = conn.execute("""
        SELECT
            p.name,
            t.name,
            l.name,
            COALESCE(pss.matches_played, 0),
            COALESCE(pss.assists, 0),
            COALESCE(pss.goals, 0)
        FROM player p
        JOIN team t ON p.team_id = t.team_id
        JOIN league l ON t.league_id = l.league_id
        LEFT JOIN player_season_stats pss ON p.player_id = pss.player_id
        ORDER BY pss.assists DESC, pss.goals DESC, p.name ASC
        LIMIT ?;
    """, (limit,)).fetchall()

    print(f"{'#':>2}  {'Igralec':<24} {'Ekipa':<18} {'Liga':<16} {'Tekme':>5} {'A':>3} {'G':>3}")
    for i, (player, team, league, matches, assists, goals) in enumerate(rows, start=1):
        print(f"{i:>2}  {player:<24} {team:<18} {league:<16} {matches:>5} {assists:>3} {goals:>3}")


def dodaj_ligo(conn):
    print("\n--- NOVA LIGA ---")
    name = input("Ime lige: ").strip()
    season = input("Sezona: ").strip()

    if not name or not season:
        print("Ime lige in sezona ne smeta biti prazna.")
        return

    liga = League(None, name, season)

    try:
        with conn:
            liga.vstavi(conn)
        print("Liga dodana.")
    except sqlite3.IntegrityError:
        print("Ta liga za to sezono že obstaja.")


def dodaj_ekipo(conn):
    print("\n--- NOVA EKIPA ---")
    league_id = input("ID lige: ").strip()
    name = input("Ime ekipe: ").strip()
    city = input("Mesto: ").strip()
    stadium = input("Stadion: ").strip()
    founded_year = input("Leto ustanovitve: ").strip()

    if not league_id.isdigit():
        print("ID lige mora biti število.")
        return

    if not name:
        print("Ime ekipe ne sme biti prazno.")
        return

    liga = League.poisci_po_id(conn, int(league_id))
    if liga is None:
        print("Liga ne obstaja.")
        return

    leto = None
    if founded_year != "":
        if not founded_year.isdigit():
            print("Leto ustanovitve mora biti število.")
            return
        leto = int(founded_year)

    ekipa = Team(None, int(league_id), name, city or None, stadium or None, leto)

    try:
        with conn:
            ekipa.vstavi(conn)
        print("Ekipa dodana.")
    except sqlite3.IntegrityError:
        print("Ta ekipa v tej ligi že obstaja.")


def dodaj_igralca(conn):
    print("\n--- NOV IGRALec ---")
    team_id = input("ID ekipe: ").strip()
    name = input("Ime igralca: ").strip()
    age = input("Starost: ").strip()
    nationality = input("Narodnost: ").strip()
    position = input("Pozicija: ").strip()

    if not team_id.isdigit():
        print("ID ekipe mora biti število.")
        return

    if not name:
        print("Ime igralca ne sme biti prazno.")
        return

    ekipa = Team.poisci_po_id(conn, int(team_id))
    if ekipa is None:
        print("Ekipa ne obstaja.")
        return

    starost = None
    if age != "":
        if not age.isdigit():
            print("Starost mora biti število.")
            return
        starost = int(age)

    igralec = Player(
        None,
        int(team_id),
        name,
        starost,
        nationality or None,
        position or None
    )

    try:
        with conn:
            igralec.vstavi(conn)
        print("Igralec dodan.")
    except sqlite3.IntegrityError:
        print("Ta igralec v tej ekipi že obstaja.")


def meni():
    print("\n===== MENI =====")
    print("1 - Izpiši vse lige")
    print("2 - Izpiši vse ekipe")
    print("3 - Dodaj ligo")
    print("4 - Izpiši vse igralce")
    print("5 - Izpiši vse tekme")
    print("6 - Izpiši ekipe po ligi")
    print("7 - Izpiši igralce po ekipi")
    print("8 - Izpiši tekme po ligi")
    print("9 - Dodaj ekipo")
    print("10 - Dodaj igralca")
    print("11 - Izpiši lestvico lige")
    print("12 - Izpiši top strelce")
    print("13 - Izpiši top asistente")
    print("0 - Izhod")


def main():
    conn = sqlite3.connect("nogomet.db")
    conn.execute("PRAGMA foreign_keys = ON;")

    while True:
        meni()
        izbira = input("Izbira: ").strip()

        if izbira == "1":
            izpisi_lige(conn)
        elif izbira == "2":
            izpisi_ekipe(conn)
        elif izbira == "3":
            dodaj_ligo(conn)
        elif izbira == "4":
            izpisi_igralce(conn)
        elif izbira == "5":
            izpisi_tekme(conn)
        elif izbira == "6":
            izpisi_ekipe_po_ligi(conn)
        elif izbira == "7":
            izpisi_igralce_po_ekipi(conn)
        elif izbira == "8":
            izpisi_tekme_po_ligi(conn)
        elif izbira == "9":
            dodaj_ekipo(conn)
        elif izbira == "10":
            dodaj_igralca(conn)
        elif izbira == "11":
            izpisi_lestvico_lige(conn)
        elif izbira == "12":
            izpisi_top_strelce(conn)
        elif izbira == "13":
            izpisi_top_asistente(conn)
        elif izbira == "0":
            print("Izhod iz programa.")
            break
        else:
            print("Neveljavna izbira.")

    conn.close()


if __name__ == "__main__":
    main()
