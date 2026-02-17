import sqlite3
from src.baza import League, Team


def izpisi_lige(conn):
    print("\n--- LIGE ---")
    for liga in League.poisci_vse(conn):
        print(f"{liga.league_id}: {liga.name} ({liga.season})")


def izpisi_ekipe(conn):
    print("\n--- EKIPE ---")
    for ekipa in Team.poisci_vse(conn):
        print(f"{ekipa.team_id}: {ekipa.name} (liga {ekipa.league_id})")


def dodaj_ligo(conn):
    print("\n--- NOVA LIGA ---")
    name = input("Ime lige: ")
    season = input("Sezona: ")

    liga = League(None, name, season)
    liga.vstavi(conn)
    print("Liga dodana!")


def meni():
    print("\n===== MENI =====")
    print("1 - Izpiši vse lige")
    print("2 - Izpiši vse ekipe")
    print("3 - Dodaj ligo")
    print("0 - Izhod")


def main():
    conn = sqlite3.connect("nogomet.db")

    while True:
        meni()
        izbira = input("Izbira: ")

        if izbira == "1":
            izpisi_lige(conn)
        elif izbira == "2":
            izpisi_ekipe(conn)
        elif izbira == "3":
            dodaj_ligo(conn)
        elif izbira == "0":
            print("Izhod iz programa.")
            break
        else:
            print("Neveljavna izbira!")

    conn.close()


if __name__ == "__main__":
    main()
