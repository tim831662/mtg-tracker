# MTG Tracker

Class project for exploring Magic: The Gathering tournament results, decklists,
and metagame statistics. This branch contains the project skeleton only.

## Stack

- Python 3.12+, FastAPI, and Jinja templates for a small web application
- PostgreSQL, SQLAlchemy, psycopg, and Alembic for persistence and migrations
- Separate Python importers for Scryfall bulk files and MTG_decklistcache JSON
- pytest and Ruff for development checks

## Get started

Install Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Clone the repository and check out the branch containing this skeleton
(`chore/project-skeleton`, or `main` after it is merged). The branch must be pushed
to GitHub before teammates can fetch it.

Run these commands from the repository root:

```powershell
uv sync --locked --extra dev
Copy-Item .env.example .env
uv run python -m uvicorn mtg_tracker.main:app --app-dir backend
```

On macOS/Linux, use `cp .env.example .env` for the copy step.

Keep the example `.env` values as they are for now. No PostgreSQL installation,
Docker, database account, or real database credentials are needed to run the
skeleton. The example username/password are reserved for the optional local
database setup below.

Open <http://127.0.0.1:8000> for the screen placeholders and
<http://127.0.0.1:8000/docs> for API documentation. The shell and health endpoint
run without a database connection. `/api/health` reports application liveness only.
Feature endpoints read from PostgreSQL and need a database with the migration
applied and data imported (see below).

Implemented JSON API endpoints (full contract with example responses in
[docs/api-contract.md](docs/api-contract.md)):

- `GET /api/decks` and `GET /api/decks/{id}` — browse decks, filter by
  `format` or `archetype`, paginate; deck detail includes the card list and
  tournament appearances.
- `GET /api/tournaments` and `GET /api/tournaments/{id}` — browse
  tournaments, filter by `format`; detail includes final standings.
- `GET /api/analytics/matchups` — matchup win rates by archetype pair,
  filterable by `format` or `tournament_id`.

Leave the terminal running while using the site. Press Ctrl+C to stop it, then
run the startup command again after editing Python files. Automatic restart via
`--reload` is optional; the default above uses the startup mode verified locally.

## Database setup (when needed)

For a local database, install Docker and run:

```powershell
docker compose up -d db
```

The development credentials and port in `.env.example` match `compose.yaml`.
Alternatively, set `DATABASE_URL` in `.env` to a team PostgreSQL database using
the `postgresql+psycopg://` URL scheme. Add the provider's required SSL options.
Keep real credentials out of Git.

Apply the existing migration and load the sample tournament data so the API
endpoints return real records:

```powershell
uv run alembic upgrade head
uv run python -m mtg_tracker.importers.tournaments database/seeds/sample_tournament_data.json
```

Note that the sample importer does not load match results yet (the seed file's
matches reference entries that are not present), so matchup analytics stay
empty until real match data is imported. Coordinate migrations before applying
them to a shared class database.

## Structure

```text
backend/mtg_tracker/
  api/             JSON API routes for decks, tournaments, and analytics
  core/            Environment configuration
  db/              SQLAlchemy base and session factory
  models/          Relational mappings
  schemas/         Pydantic request/response contracts (frontend API contract)
  repositories/    Database queries, including matchup win-rate SQL
  services/        Validation and analytics logic
  importers/       Separate batch-import entry points
  web/             Page routes, shared templates, and CSS
database/
  migrations/      Alembic setup and the initial schema migration
  queries/         Reviewed analytical SQL (matchup win rates)
  seeds/           Small, synthetic development fixtures
docs/              Scope, architecture, schema decisions, and team workflow
tests/             Shell smoke tests and seeded API contract tests
```

## Development

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python -m mtg_tracker.importers.scryfall --help
uv run python -m mtg_tracker.importers.tournaments --help
```

Import commands expose help only; attempting an import exits with an explicit
not-implemented message. Nothing is downloaded or written to the database.

Read [scope](docs/scope.md), [architecture](docs/architecture.md),
[database design notes](docs/database-design.md), and
[contribution guidance](CONTRIBUTING.md) before adding features.
