import sqlite3
from src.baza import ustvari_bazo


def main():
    conn = sqlite3.connect("nogomet.db")
    conn.execute("PRAGMA foreign_keys = ON;")

    with conn:
        ustvari_bazo(conn)

    conn.close()
    print("Baza je bila uspešno ustvarjena: nogomet.db")


if __name__ == "__main__":
    main()