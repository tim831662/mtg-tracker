# MTG Tracker

A class project for exploring Magic: The Gathering decks, tournaments, and match results.

## Requirements

- Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 22.12+ and npm
- Docker Desktop, installed and running

## First-time setup

Open a terminal in the `mtg-tracker` folder. The application code is on `main`.

<details>
<summary>Need to download the project?</summary>

Install Git, then run:

```powershell
git clone https://github.com/tim831662/mtg-tracker.git
cd mtg-tracker
```

</details>

**Already have a database from before the UUID schema update?** Follow the
[backup and upgrade instructions](docs/schema-integration.md#upgrade-an-existing-application-database)
before running the migration below.

With Docker Desktop running, run these commands from the project folder.
The commands below use PowerShell.

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

## Run the app

In one terminal, from the project folder:

```powershell
docker compose up -d --wait db
uv run python -m uvicorn mtg_tracker.main:app --app-dir backend
```

Keep it running. In a second terminal, from the project folder:

```powershell
cd frontend
npm run dev
```

Open the URL Vite prints, usually **http://127.0.0.1:5173**.
In **Deck Browser**, look for **Connected to the backend API** and the six imported decks.
The API documentation is at http://127.0.0.1:8000/docs.

Use these same startup commands next time. Stop each server with **Ctrl+C**.
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
