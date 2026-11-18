# API contract

The FastAPI JSON API lives under `/api`. The React development server proxies
that prefix to FastAPI. `/docs` and `/openapi.json` describe the same Pydantic
response models used by the routes.

## Shared conventions

- Entity IDs are UUID strings. Malformed IDs return 422; unknown valid UUIDs
  return 404 on detail endpoints.
- List responses are `{ "items": [...], "total": 0, "limit": 20, "offset": 0 }`.
  `total` ignores pagination. Limit defaults to 20 and is capped at 100.
- Dates are calendar dates, `YYYY-MM-DD`, matching `tournament.occurred`.
- Format filters use the normalized format name (for example `Standard`).
- Error bodies follow FastAPI's `detail` convention.
- Standings identify entries by `(player_id, tournament_id)`. There is no
  separate `entry_id` in the selected schema.

This is an intentional contract change from numeric IDs and timestamp-formatted
calendar dates. The existing React browser already treats IDs as opaque URL
values; no new UI features are included in the schema integration.

## GET /api/decks

Optional parameters: `format`, `archetype`, `limit`, `offset`.

```json
{
  "items": [
    {
      "id": "00000000-0000-0000-0000-000000000001",
      "name": "Mono Red",
      "format": "Standard",
      "archetype": "Aggro"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

The summary does not include player, event, or results. Those remain available
through deck appearances and tournament standings.

## GET /api/decks/{deck_id}

Returns the deck summary fields plus:

- `cards`: objects with `name`, `quantity`, `zone` (`main` or `sideboard`), and
  nullable `mana_cost` containing the original text.
- `maindeck_size`, `sideboard_size`: summed quantities in each zone.
- `appearances`: objects with UUID `tournament_id`, `tournament_name`, calendar
  `tournament_date`, UUID `player_id`, `player_name`, and nullable `final_placement`.

## GET /api/tournaments

Optional parameters: `format`, `limit`, `offset`. Newest events come first.
Each item has UUID `id`, `name`, `format`, calendar `date`, nullable `location`,
`num_rounds`, and `player_count` (the count of stored entries).

## GET /api/tournaments/{tournament_id}

Returns those summary fields and `standings`, ordered by placement (nulls last):

```json
{
  "tournament_id": "00000000-0000-0000-0000-000000000002",
  "player_id": "00000000-0000-0000-0000-000000000003",
  "player_name": "Alice",
  "deck_id": "00000000-0000-0000-0000-000000000001",
  "deck_name": "Mono Red",
  "archetype": "Aggro",
  "seed": 1,
  "final_placement": 2
}
```

## GET /api/analytics

Returns `{ "endpoints": ["matchups"] }`.

## GET /api/analytics/matchups

Optional parameters: `format`, UUID `tournament_id`, and positive `min_matches`
(default 1). Response: `{ "items": [...] }`, with each item containing
`archetype_a`, `archetype_b`, `matches_played`, `wins_a`, `wins_b`, `draws`, and
`win_rate_a` rounded to four decimal places.

Only `done = true` matches with two players count. More game wins determines the
match winner; equal game wins means a match draw. Draws count in matches played
but neither side's wins. `win_rate_a = wins_a / matches_played`.

A/B follows the schema's canonical player UUID order (`playera > playerb`), not
archetype name order. Archetypes can consequently appear in either direction.
The portable application query lives in `repositories/matchups.py`; the matching
PostgreSQL query is in `database/queries/matchup_win_rates.sql`.

## Remaining feature work

Real tournament/match ingestion, catalog enrichment, dashboard aggregates, and
server-side text search are not completed by the schema integration.
