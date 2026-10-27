# Contributing

Create a focused branch from an up-to-date `main` (for example,
`feat/deck-browser` or `chore/initial-schema`). Keep generated imports,
credentials, virtual environments, and database dumps out of Git.

Before opening a pull request, run the Ruff and pytest commands in the README.
Describe the behavior changed and checks run. Keep changes small enough for a
classmate to review. Open a pull request into `main` and get a teammate's review.

For schema changes, commit the Alembic migration with the model change. Inspect
generated SQL and agree on shared-database updates with the team. Use a personal
or local database for development. Keep analysis queries in `database/queries/`
so the database work is visible and reviewable.
