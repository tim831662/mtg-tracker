# Current implementation scope

Included: a React frontend with four navigation targets, Dashboard and Deck
Browser layouts, labeled placeholder features, FastAPI database-backed deck and
tournament endpoints, initial matchup analytics, and the selected 17-table UUID
PostgreSQL schema with ORM mappings, initialization, and a legacy-data migration.

The existing normalized-JSON importer still loads sample tournaments, players,
cards, decks, and entries. Match importing is explicitly unfinished. Catalog
tables exist, but direct card-source parsing/enrichment remains separate work.

This schema integration keeps the intermediate UI scope. It does not complete
the Dashboard's live aggregates, Deck Details UI, Statistics UI, real tournament
source integration, authentication, community submissions, or deployment.

Use `docs/schema-integration.md` and `docs/api-contract.md` as the current schema
and API references. Older Task 3 implementation/checklist files predate this
integration and should not be used to infer current feature completion.
