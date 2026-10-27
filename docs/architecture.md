# Architecture

One Python application serves the API and simple Jinja HTML pages. This follows
the brief's FastAPI/Python direction and keeps the initial project free of a
separate JavaScript toolchain. A richer frontend can be added later if needed.

Request flow when implemented:

```text
HTML pages / API -> schemas -> services -> repositories -> PostgreSQL
Local JSON files -> importers -> services / repositories -> PostgreSQL
```

`main.py` composes the application. `core` reads environment settings. `db` owns
SQLAlchemy metadata and lazy session setup. `models` defines tables; `schemas`
defines public contracts. Services own validation, calculations, and transaction
boundaries. Repositories own queries. API routes handle HTTP concerns. Web routes
render templates. Avoid importing API or web modules into the persistence layer.

Alembic owns schema changes; the application does not create tables at startup.
Future model modules must be imported in `models/__init__.py` for Alembic discovery.
Application liveness and page placeholders intentionally need no database access.

Source integrations are batch jobs, separate from web requests. The planned
Scryfall importer reads a previously downloaded bulk file; the tournament importer
reads a local MTG_decklistcache checkout. Add cleaning, rejected-record reporting,
source provenance, and idempotency before importing real data. Source schemas and
access policies must be checked when implementing those integrations.
