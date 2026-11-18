# MTG Tracker

Class project for exploring Magic: The Gathering tournament results, decklists,
and metagame statistics. The current integration uses the selected **17-table,
UUID-based PostgreSQL schema** from the `schema` branch.

## Requirements

- Git
- Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 22.12+ and npm
- Docker Desktop, installed and running, for the local PostgreSQL setup below

## 1. Get the integration code

Use `main` for the integrated application. For a new checkout:

```powershell
git clone https://github.com/tim831662/mtg-tracker.git
cd mtg-tracker
```

For an existing checkout, save or commit your own changes before switching:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
```

Do not use the standalone `schema` branch as the application checkout. Its design
has been integrated here with the matching backend, importer, and migration.

## 2. Install dependencies and configure the environment

Run from the repository root:

```powershell
uv sync --locked --extra dev
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

On macOS/Linux, use `test -f .env || cp .env.example .env` for the copy step.
The example values are development credentials for the Docker database. Keep
real credentials and `.env` out of Git.

If reusing an existing `.env`, check that its local database host is
`127.0.0.1` and that `POSTGRES_PORT` matches the port in `DATABASE_URL`.
The defaults are:

```dotenv
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://mtg:mtg_local@127.0.0.1:5432/mtg_tracker
```

## 3. Start PostgreSQL

Open Docker Desktop and wait for its engine to be running. From the repository root:

```powershell
docker compose up -d db
docker compose ps
```

Wait until the database reports **healthy**. If Windows refuses port 5432 or the
port is already occupied, choose an available port, such as 55432, and change
both `POSTGRES_PORT` and the port inside `DATABASE_URL` in `.env`. Then rerun
`docker compose up -d db`. Use `127.0.0.1` rather than `localhost` to match the
Docker IPv4 binding.

For a managed PostgreSQL database, set `DATABASE_URL` to its
`postgresql+psycopg://` connection URL with the provider's SSL options; skip the
Docker commands. Coordinate upgrades before using a shared team database.

## 4. Upgrade the schema and load sample records

**Existing databases:** stop the old backend and take a PostgreSQL backup before
upgrading. For the local Docker database, these PowerShell commands save a backup
under the ignored `tmp` directory without piping binary data through the shell:

```powershell
New-Item -ItemType Directory -Force tmp | Out-Null
$taskBackupName = "before_uuid_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".dump"
docker compose exec -T db pg_dump -U mtg -d mtg_tracker -Fc -f "/tmp/$taskBackupName"
docker compose cp "db:/tmp/$taskBackupName" "tmp/$taskBackupName"
```

For managed databases, use the provider's backup procedure. A brand-new database
does not need this backup step.

For both fresh and existing application databases, run:

```powershell
uv run alembic upgrade head
uv run alembic current
uv run python -m mtg_tracker.importers.tournaments database/seeds/sample_tournament_data.json
```

The revision should be **`002_adopt_schema_branch (head)`**. The importer should
finish with **`Import completed successfully`**. It loads two synthetic sample
tournaments and six decks; rerunning it recognizes these existing records.
Match importing is unfinished, so the sample import does not populate matchup
statistics.

The migration transfers compatible old records to the selected schema in one
transaction. If a record violates the new constraints, the migration rolls back;
fix the reported data rather than deleting the database. Automatic downgrade is
unsupported: recovery uses the pre-upgrade backup. See
[schema integration](docs/schema-integration.md) for details.

Use Alembic for application initialization. Do not also run
`database/queries/schema/mtg_schema.pgsql` against the same database; that script
is an alternative initializer for empty-database experiments.

## 5. Start the backend

In the first terminal, from the repository root:

```powershell
uv run python -m uvicorn mtg_tracker.main:app --app-dir backend
```

Wait for **`Application startup complete`**. Keep this terminal running.
API documentation is at <http://127.0.0.1:8000/docs>. The pages directly on port
8000 are the earlier Jinja placeholders; use port 5173 for the React frontend.

## 6. Start the React frontend

Open a second terminal at the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open the Local URL Vite prints, normally <http://127.0.0.1:5173>.
Vite forwards `/api` requests to the backend on port 8000. Keep this terminal
running too. Repeat `npm ci` after dependency changes; it is not required on
every subsequent startup.

## 7. Confirm it works

- Open **Deck Browser**. It should say **Connected to the backend API**. A fresh
  database shows **6 shown · 6 total** after the sample import; an existing
  database can contain additional records.
- Deck names include **Azorius Control - David's Build** and **Izzet Control - Alice's Build**.
- If it says **Showing sample decks**, it is using the frontend fallback. Check
  the backend terminal and database setup, then click **Reload API**.
- <http://127.0.0.1:8000/api/health> should return `{ "status": "ok" }`. This is
  application liveness only; the deck endpoint checks actual database access.
- <http://127.0.0.1:8000/api/decks> should return database records with UUID IDs.
- Dashboard and Deck Browser layouts work; Deck Details and Statistics remain
  navigation placeholders. Dashboard figures are labeled samples. Player, event,
  and result columns show dashes because the deck summary API does not include them.

Stop the backend and frontend with Ctrl+C in their terminals. Stop the local
database with `docker compose stop db`; its data remains in the Docker volume.
To resume later, start the database and run the two server commands again.

## Development checks

From the repository root:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

From `frontend`:

```powershell
npm test
npm run build
```

Without `TEST_DATABASE_URL`, regular tests use SQLite and six PostgreSQL migration
checks are skipped. To test on PostgreSQL locally, create a dedicated test database
once, then derive its port from Docker (omit `createdb` if it already exists):

```powershell
docker compose exec -T db createdb -U mtg mtg_tracker_test
$taskTestDbAddress = (docker compose port db 5432).Trim()
$env:TEST_DATABASE_URL = "postgresql+psycopg://mtg:mtg_local@$taskTestDbAddress/mtg_tracker_test"
uv run pytest
Remove-Item Env:TEST_DATABASE_URL
```

Tests create and remove randomly named schemas inside the test database.
GitHub checks supply PostgreSQL and run these checks automatically.

See [API contract](docs/api-contract.md), [schema integration](docs/schema-integration.md),
[architecture](docs/architecture.md), and [contribution guidance](CONTRIBUTING.md).
The importer still needs direct real-tournament parsing, match importing, and
Scryfall/card-catalog enrichment. The UI and deployment also remain intermediate.
Older Task 3 checklist files predate this integration; use the linked documents
for the current schema and API.
