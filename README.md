# MTG Tracker

A class project for exploring Magic: The Gathering decks, tournaments, and match results.

## Requirements

Install Git, Python 3.12+, [uv](https://docs.astral.sh/uv/getting-started/installation/),
Node.js 22.12+ (includes npm), and Docker Desktop. Open Docker Desktop before setup
or startup. The commands below use Windows PowerShell.

## Set up the project

If you have a copy from before the schema update, stop the app and save any local
work or backups outside that folder. In the old project folder, run
`docker compose down --volumes` to remove its local database, then close the
project and delete its folder using File Explorer. This gives you a fresh local
setup and deletes the old local database records.

Open PowerShell in the folder where you keep your projects and run:

```powershell
git clone https://github.com/tim831662/mtg-tracker.git
cd mtg-tracker
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The setup file installs dependencies, creates `.env`, starts PostgreSQL, creates
or updates the tables, and loads two sample tournaments with six decks. Wait for
**Setup complete**, then start the app below. You can rerun the setup command
if it stops with an error or after pulling updates. Existing `.env` settings
and database records are preserved when rerunning setup.

## Run the app

If you already completed setup, start here. With Docker Desktop running, open
PowerShell in the `mtg-tracker` folder and run:

```powershell
docker compose up -d --wait db
uv run python -m uvicorn mtg_tracker.main:app --app-dir backend
```

Keep that terminal running. Open a second PowerShell terminal in the same project folder:

```powershell
cd frontend
npm run dev
```

Open the URL Vite prints, usually **http://127.0.0.1:5173**.
In **Deck Browser**, look for **Connected to the backend API**.
API documentation is at http://127.0.0.1:8000/docs.

Use these same commands each time you start the app. Stop each server with
**Ctrl+C**. To stop PostgreSQL and keep its data, run `docker compose stop db`
from the project folder.

To get updates, stop the app and save or commit your work, then run these from
the project folder before starting the app again:

```powershell
git pull --ff-only
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

## Troubleshooting

- **Setup stops** — Read the error above “Setup stopped”, fix it, then rerun setup.
  Check that Docker Desktop is running and all requirements are installed.
- **Database port error** — In `.env`, change `POSTGRES_PORT` and the port in
  `DATABASE_URL` to the same available port, such as `55432`. Keep the database
  host as `127.0.0.1`, then rerun setup.
- **Deck Browser says “Showing sample decks”** — Check that the backend started
  successfully and setup finished. Click **Reload API**.

## Current progress

Deck Browser displays database records. Dashboard figures use labeled samples,
while Deck Details and Statistics have placeholder pages. The sample tournament
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
[database details](docs/schema-integration.md),
[architecture](docs/architecture.md), and [contribution guide](CONTRIBUTING.md).
Older Task 3 checklist files predate the current schema. Use these linked documents
for the current setup and API.
