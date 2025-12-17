# Pet največjih evropskih nogometnih lig

## Namen projekta
Program predstavlja sistem za upravljanje sezonskih podatkov petih največjih evropskih nogometnih lig:
Premier League, La Liga, Bundesliga, Serie A in Ligue 1.

## Funkcionalnosti
- pregled lig
- pregled ekip v ligi
- pregled igralcev v ekipi
- pregled tekem v ligi
- prikaz statistike tekme
- iskanje po izbranih kriterijih (po dogovoru/nadaljevanju)

## Opis baze (ER model)
Tabela **league**: liga in sezona.  
Tabela **team**: ekipe, povezane na ligo (league_id).  
Tabela **player**: igralci, povezani na ekipo (team_id).  
Tabela **match**: tekme v ligi (league_id) z domačo in gostujočo ekipo (home_team_id, away_team_id).  
Tabela **match_stats**: statistika tekme (1:1 z match).  
Tabela **player_match_stats**: statistika igralca na tekmi (povezovalna tabela player–match).
