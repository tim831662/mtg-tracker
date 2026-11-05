# API contract

JSON API for the MTG Tracker frontend. All endpoints live under the `/api`
prefix; the HTML pages (`/`, `/decks`, `/tournaments`) are separate and return
HTML. Interactive documentation (OpenAPI/Swagger) is served at `/docs` and the
machine-readable schema at `/openapi.json` while the server runs.

Every response model here is also defined in code under
`backend/mtg_tracker/schemas/`, so the OpenAPI schema is the source of truth
if this document drifts.

## Conventions

- **List envelope**: every list endpoint returns
  `{ "items": [...], "total": <int>, "limit": <int>, "offset": <int> }`.
  `total` is the number of records matching the filters (ignoring
  pagination), so you can compute page counts.
- **Pagination**: `limit` (default 20, max 100) and `offset` (default 0)
  query parameters on list endpoints.
- **Filters**: `format` (e.g. `Standard`, `Pioneer`, case-sensitive exact
  match) on decks, tournaments, and matchups.
- **Dates**: ISO 8601 strings (e.g. `"2024-03-15T00:00:00"`).
- **Errors**: FastAPI style — `{"detail": "<message>"}` with an appropriate
  status code. Unknown IDs return `404`.
- **IDs**: integer database keys.

## GET /api/decks

List decks. Query parameters: `format`, `archetype`, `limit`, `offset`.

```json
{
  "items": [
    {"id": 1, "name": "Mono Red", "format": "Standard", "archetype": "Aggro"},
    {"id": 2, "name": "Azorius Control", "format": "Standard", "archetype": "Control"}
  ],
  "total": 2,
  "limit": 20,
  "offset": 0
}
```

## GET /api/decks/{deck_id}

One deck with its card list and tournament appearances. `cards` is a flat
list; group by `zone` (`"main"` / `"sideboard"`) in the UI.
`maindeck_size` / `sideboard_size` are the summed quantities per zone.

```json
{
  "id": 1,
  "name": "Mono Red",
  "format": "Standard",
  "archetype": "Aggro",
  "cards": [
    {"name": "Lightning Bolt", "quantity": 4, "zone": "main", "mana_cost": "{R}"}
  ],
  "maindeck_size": 4,
  "sideboard_size": 0,
  "appearances": [
    {
      "tournament_id": 1,
      "tournament_name": "Standard Showdown",
      "tournament_date": "2024-03-15T00:00:00",
      "player_id": 1,
      "player_name": "Alice",
      "final_placement": 2
    }
  ]
}
```

## GET /api/tournaments

List tournaments, newest first. Query parameters: `format`, `limit`,
`offset`. `player_count` is the number of recorded entries.

```json
{
  "items": [
    {
      "id": 2,
      "name": "Pioneer Preliminary",
      "format": "Pioneer",
      "date": "2024-04-20T00:00:00",
      "location": "Convention Center",
      "num_rounds": 6,
      "player_count": 2
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

## GET /api/tournaments/{tournament_id}

One tournament with its standings, ordered by `final_placement`
(nulls last). `final_placement` and `seed` may be `null`.

```json
{
  "id": 1,
  "name": "Standard Showdown",
  "format": "Standard",
  "date": "2024-03-15T00:00:00",
  "location": "Game Store",
  "num_rounds": 5,
  "player_count": 4,
  "standings": [
    {
      "entry_id": 2,
      "player_id": 2,
      "player_name": "Bob",
      "deck_id": 2,
      "deck_name": "Azorius Control",
      "archetype": "Control",
      "seed": 2,
      "final_placement": 1
    }
  ]
}
```

## GET /api/analytics

Index of analytics resources: `{"endpoints": ["matchups"]}`.

## GET /api/analytics/matchups

Matchup win rates by archetype pair, most-played pairs first. Query
parameters: `format`, `tournament_id`, `min_matches` (default 1).

Definitions agreed with the data model (see
`database/queries/matchup_win_rates.sql`):

- Byes (matches without an opponent) are **excluded**.
- Drawn matches count toward `matches_played` but toward neither side's
  wins, so `win_rate_a = wins_a / matches_played`.
- Rows are **directional**: `("Aggro", "Control")` covers matches where the
  Aggro player was seated as player one. The reverse pair is a separate row.
- Decks without an archetype fall back to the deck name.

```json
{
  "items": [
    {
      "archetype_a": "Aggro",
      "archetype_b": "Control",
      "matches_played": 3,
      "wins_a": 2,
      "wins_b": 1,
      "draws": 0,
      "win_rate_a": 0.6667
    }
  ]
}
```

## Suggested follow-ups (not implemented yet)

- Text search on deck/player names.
- Metagame share (`archetype` counts per tournament/format).
- Card frequency among top-8 decklists.
