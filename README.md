# MTG Tracker

A class project for exploring Magic: The Gathering decks, tournaments, and match results.

## Requirements

- Git
- Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 22.12+ and npm
- Docker Desktop, installed and running

## Setup and startup

These commands use PowerShell. Start Docker Desktop before continuing.

**1. Start fresh.** If you already have a copy, stop the frontend and backend with
Ctrl+C. Save any local work, `.env` settings, or database backups you need outside
the old folder. From the old `mtg-tracker` folder, run:

```powershell
docker compose down --volumes
```

This deletes the project's local Docker database so it can be recreated.
Close the old project and delete its `mtg-tracker` folder using File Explorer.
If this is your first download, start with the clone commands below.

Open a terminal in the folder where you keep your projects and run:

```powershell
git clone https://github.com/tim831662/mtg-tracker.git
cd mtg-tracker
```

**2. Install dependencies and create the database.** From the newly cloned
`mtg-tracker` folder, run:

```powershell
uv sync --locked --extra dev
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d --wait db
uv run alembic upgrade head
uv run python -m mtg_tracker.importers.tournaments database/seeds/sample_tournament_data.json
```

This installs the Python dependencies, starts PostgreSQL, creates the tables,
and loads two sample tournaments with six decks. Then install the frontend dependencies:

```powershell
cd frontend
npm ci
cd ..
```

**3. Start the backend.** From the project folder:

```powershell
docker compose up -d --wait db
uv run python -m uvicorn mtg_tracker.main:app --app-dir backend
```

**4. Start the frontend.** Keep the backend running. In a second terminal,
from the project folder:

```powershell
cd frontend
npm run dev
```

Open the URL Vite prints, usually **http://127.0.0.1:5173**.
In **Deck Browser**, look for **Connected to the backend API** and the six imported decks.
The API documentation is at http://127.0.0.1:8000/docs.

**For later runs**, keep your existing folder and open a terminal there. With
Docker Desktop running and the app stopped, save or commit local changes before
pulling. If your database predates the UUID schema update, follow the
[backup instructions](docs/schema-integration.md#upgrade-an-existing-application-database)
before running the migration. Then run:

```powershell
git pull --ff-only
uv sync --locked --extra dev
docker compose up -d --wait db
uv run alembic upgrade head
cd frontend
npm ci
cd ..
uv run python -m uvicorn mtg_tracker.main:app --app-dir backend
```

Use a second terminal for `cd frontend` followed by `npm run dev`, as in step 4.

Stop each server with **Ctrl+C**.
To stop PostgreSQL and keep its data, run `docker compose stop db` from the project folder.

## Troubleshooting

- **Database port error** — In `.env`, change `POSTGRES_PORT` and the port in
  `DATABASE_URL` to the same available port, such as `55432`. Keep the database
  host as `127.0.0.1`, then rerun `docker compose up -d --wait db`.
- **Deck Browser says “Showing sample decks”** — Check that the backend started
  successfully and that the setup commands finished. Click **Reload API**.
- **Dependencies changed after pulling** — Run `uv sync --locked --extra dev`
  from the project folder and `npm ci` from `frontend`.
- **Using macOS/Linux** — Replace the PowerShell `.env` copy command with
  `test -f .env || cp .env.example .env`.

## Current progress

Deck Browser displays database records. Dashboard figures use labeled samples,
and Deck Details and Statistics have placeholder pages. The sample tournament
import uses synthetic records and currently skips matches.

## Development checks

From the project folder:

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

See the [API contract](docs/api-contract.md),
[database setup and PostgreSQL checks](docs/schema-integration.md),
[architecture](docs/architecture.md), and [contribution guide](CONTRIBUTING.md).
Older Task 3 checklist files predate the current schema. Use these linked documents
for the current setup and API.
