# Architecture

React and plain CSS in `frontend/` provide the UI. Vite proxies `/api` to the
FastAPI backend on port 8000. The earlier Jinja HTML placeholders remain at the
backend's page routes; the React UI runs on Vite's port.

```text
React -> API schemas -> services -> repositories -> selected PostgreSQL schema
JSON files -> tournament importer -> the same ORM mappings and database
```

The selected schema is the 17-table UUID design from the `schema` branch. The
active mappings are `models/catalog.py` and `models/tournament.py`; both are
registered in `models/__init__.py`. Python attribute names map to the design's
physical names, for example `Deck.id` to `deck.pk_deck`.

Alembic owns upgrades. Revision 001 records the old schema for existing installs;
revision 002 creates the selected schema, transfers compatible data, and removes
the retired tables in a single PostgreSQL transaction. Its DDL snapshot is frozen
under `database/migrations/sql/`. The standalone initializer is an alternative
for empty database experiments, not a second application migration path.

API response formats remain separate from physical database names. Entity IDs
are UUIDs; tournament entries use composite keys. Services own business logic,
repositories own queries, and routes own HTTP validation and serialization.
The API contract and schema integration documents describe the intentional
changes and compatibility extensions.

The existing tournament importer accepts the project's normalized JSON. Direct
MTG_decklistcache parsing, match importing, and catalog enrichment remain future
work. Batch importing stays separate from HTTP requests.
