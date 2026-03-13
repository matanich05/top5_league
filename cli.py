import sqlite3
from src.baza import League, Team, Player, Match


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
        elif izbira == "0":
            print("Izhod iz programa.")
            break
        else:
            print("Neveljavna izbira.")

    conn.close()


if __name__ == "__main__":
    main()