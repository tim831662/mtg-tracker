# Database design

The selected design is the UUID-based, 17-table schema from the `schema` branch
at `b844754`. It is now implemented by the ORM and Alembic revision
`002_adopt_schema_branch`.

See [schema integration](schema-integration.md) for the complete table list,
physical-to-application mappings, corrections, compatibility extensions, legacy
data transfer, and upgrade procedure.

- UUID primary keys identify players, decks, cards, artists, formats, tournaments,
  and matches. Mana and rarity retain small numeric lookup keys.
- Entries use `(player, tournament)`. Other associations use composite keys.
- Deck-card membership adds `zone` to the original key to preserve main-deck and
  sideboard quantities.
- Formats are normalized records referenced by decks and tournaments.
- Match participants reference players and must also have entries in the same
  tournament. Canonical ordering prevents reversed representations of a pair.
- A completed match's game scores determine its result. Byes and incomplete
  matches are excluded from matchup aggregates.

Cross-row deck legality, exceptions for particular cards/formats, historical
legality, and comprehensive real-source validation still need feature work.
The basic validation service uses the format's minimum size and copy limit; it
is not a complete legality engine.
