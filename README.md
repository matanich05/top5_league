# Pet najvecjih evropskih nogometnih lig

## Namen projekta
Projekt je spletna aplikacija za pregled sezone 2024/2025 v petih najvecjih evropskih nogometnih ligah:
Premier League, La Liga, Bundesliga, Serie A in Ligue 1.

Aplikacija je zamisljena kot poenostavljena razlicica strani, kot sta SofaScore in FlashScore. Uporabnik lahko v brskalniku pregleduje lige, ekipe, igralce, tekme, rezultate, ligaske lestvice in osnovne statistike.

## Funkcionalnosti
- pregled vseh lig,
- pregled ekip v posamezni ligi,
- pregled igralcev v posamezni ekipi,
- pregled vseh tekem,
- filtriranje tekem po ligi, ekipi in krogu,
- iskanje tekem po imenu ekipe ali lige,
- prikaz rezultata in statistike posamezne tekme,
- izracun ligaske lestvice,
- prikaz najboljsih strelcev in asistentov,
- iskanje ekip in igralcev.

## Podatki
Podatki so shranjeni v CSV datotekah v mapi `data/`.

CSV datoteke vsebujejo pripravljene podatke za sezono 2024/2025. Iz teh datotek se zgradi SQLite baza `nogomet.db`.

## Viri podatkov
CSV datoteke so bile pripravljene na podlagi naslednjih virov:

- Rezultati tekem in statistika tekem: [football-data.co.uk](https://www.football-data.co.uk/data)
- Igralci in sezonska statistika igralcev: [Kaggle - Football players stats 2024/2025](https://www.kaggle.com/datasets/hubertsidorowicz/football-players-stats-2024-2025), ki temelji na podatkih iz [FBref](https://fbref.com/)
- Referencne strani za preverjanje podatkov: [FBref Big 5 2024/2025](https://fbref.com/en/comps/Big5/2024-2025/2024-2025-Big-5-European-Leagues-Stats)

## Opis baze
Tabela **league** hrani ligo in sezono.

Tabela **team** hrani ekipe, povezane na ligo prek `league_id`.

Tabela **player** hrani igralce, povezane na ekipo prek `team_id`.

Tabela **match** hrani tekme v ligi, domaco ekipo, gostujoco ekipo, datum in krog.

Tabela **match_stats** hrani statistiko tekme. Povezana je s tabelo `match` v razmerju 1 : 1.

Tabela **player_season_stats** hrani realno sezonsko statistiko igralcev, na primer nastope, minute, gole, asistence in kartone.

## Zagon
Najprej je treba namestiti Python in odvisnosti:

```bash
pip install -r requirements.txt
```

Nato se ustvari SQLite baza iz CSV datotek:

```bash
python main.py
```

Spletna aplikacija se zazene z:

```bash
python app.py
```

V brskalniku se odpre:

```text
http://127.0.0.1:5000/
```

## ER diagram
ER diagram prikazuje strukturo baze in povezave med tabelami.

![ER diagram](docs/er_diagram.png)
