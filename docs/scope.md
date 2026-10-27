# Skeleton scope

The supplied class brief guides the structure. Its research prompts and proposed
implementation details are context; this change only establishes a starting point.

Included: a runnable FastAPI application, four HTML screen placeholders, health
endpoint, explicit API stubs, PostgreSQL configuration, empty migration setup,
import command placeholders, documentation, and development checks.

Future work from the brief:

- Search decklists and inspect main deck/sideboard contents.
- Store players, formats, tournaments, entries, and Swiss-round match results.
- Calculate standings, leaderboards, matchup win rates, and top-8 card frequency.
- Import card/legality data and tournament JSON with validation and repeatable imports.
- Enforce agreed format-specific deck and match integrity rules in PostgreSQL.
- Revisit community submissions and account requirements after agreeing the core scope.

No models, tables, import logic, analytical SQL, authentication, live source calls,
or deployment infrastructure are implemented. The UI contains no fabricated stats.

Suggested implementation order: review the schema, add the initial migration and
synthetic fixtures, implement local-file imports, add read queries/APIs, then wire
the screens to those APIs or services. Decide submission/authentication scope separately.
