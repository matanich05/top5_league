# ER model

Ta dokument opisuje trenutno strukturo baze za projekt petih največjih evropskih nogometnih lig.

```mermaid
erDiagram
    league ||--o{ team : "ima ekipe"
    league ||--o{ match : "ima tekme"
    team ||--o{ player : "ima igralce"
    team ||--o{ match : "nastopa kot domača ekipa"
    team ||--o{ match : "nastopa kot gostujoča ekipa"
    match ||--|| match_stats : "ima statistiko"
    player ||--|| player_season_stats : "ima sezonsko statistiko"

    league {
        integer league_id PK
        varchar name
        varchar season
    }

    team {
        integer team_id PK
        integer league_id FK
        varchar name
        varchar city
        varchar stadium
        integer founded_year
    }

    player {
        integer player_id PK
        integer team_id FK
        varchar name
        integer age
        varchar nationality
        varchar position
    }

    match {
        integer match_id PK
        integer league_id FK
        integer home_team_id FK
        integer away_team_id FK
        date match_date
        integer round_number
    }

    match_stats {
        integer match_id PK,FK
        integer home_goals
        integer away_goals
        integer home_shots
        integer away_shots
        integer home_yellow
        integer away_yellow
        integer home_red
        integer away_red
    }

    player_season_stats {
        integer player_id PK,FK
        integer matches_played
        integer starts
        integer minutes_played
        integer goals
        integer assists
        integer yellow_cards
        integer red_cards
    }
```

## Komentarji relacij

- `league` in `team`: ena liga ima več ekip, vsaka ekipa pripada eni ligi.
- `league` in `match`: ena liga ima več tekem, vsaka tekma pripada eni ligi.
- `team` in `player`: ena ekipa ima več igralcev, vsak igralec je v podatkih vezan na eno ekipo v sezoni.
- `team` in `match`: vsaka tekma ima dve ekipi, domačo in gostujočo.
- `match` in `match_stats`: vsaka tekma ima natanko eno vrstico statistike tekme.
- `player` in `player_season_stats`: vsak igralec ima eno vrstico sezonske statistike.
