# Selected schema integration

The project now uses the design from the `schema` branch at `b844754`. Its
17-table design replaces the old seven-table integer-key schema. The active
SQLAlchemy mappings, Alembic migration, and standalone SQL describe this same
schema. PostgreSQL folds the original unquoted identifiers to lowercase.

| Area | Physical tables |
| --- | --- |
| Players and decks | `player`, `deck`, `card_in_deck` |
| Card catalog | `card`, `mana`, `rarity`, `artist`, `artist__worked_on__card`, `keyword`, `subtype`, `card_mana_cost`, `card_is_type` |
| Formats | `format`, `formatrestriction` |
| Competition | `tournament`, `tournamententry`, `tournament_match` |

Entity primary keys use UUIDs. `mana` and `rarity` retain their small numeric
lookup keys. `tournamententry` uses `(player, tournament)` as its primary key;
association tables use composite keys. `tournament.id` is an external source
identifier; its UUID primary key is `tournament.pk_tournament`.

## Corrections and compatibility extensions

- SQL creates referenced tables first, includes the missing comma after
  `card.title`, and indexes the correctly spelled `tournament.occurred`.
- `card.rarity` has a foreign key to the rarity lookup.
- `card_in_deck` retains the application's `zone` column. Its primary key is
  `(deck, card, zone)`, allowing a card in both main deck and sideboard. Amounts
  must be positive; zones must be `main` or `sideboard`.
- `deck.format` references `format`. Deck archetype and source IDs, player source
  IDs, tournament display name/round count/source URL, and import timestamps
  preserve the information already used by the application.
- `card.mana_cost` and `card.type_line` preserve original text from existing
  imports. The normalized catalog tables exist for the later catalog importer;
  this change does not claim to finish Scryfall or CSV importing.
- Matches reference player UUIDs, as in the selected design. Composite foreign
  keys also require participants to have entries in that same tournament.
  `playera > playerb` gives a canonical pair order; byes have no `playerb`.
- Game scores and the `done` flag determine the result. There is no separate
  winner column that could contradict those scores. Analytics ignore unfinished
  matches and byes. Draws count as played matches but neither side's win.

Python attributes such as `Deck.id` and `Deck.name` map to `deck.pk_deck` and
`deck.title`. This keeps services readable while using the chosen physical
schema. API IDs are UUID strings. Dates are `YYYY-MM-DD`. A standing identifies
its entry using `player_id` and `tournament_id`; the former integer `entry_id`
has been removed. See [the API contract](api-contract.md).

## Upgrade an existing application database

Stop the old backend and take a PostgreSQL backup before upgrading a database
created with the old schema. For the local Docker setup, start the database and
save a backup under the ignored `tmp` folder using PowerShell:

```powershell
docker compose up -d --wait db
New-Item -ItemType Directory -Force tmp | Out-Null
$taskBackupName = "before_uuid_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".dump"
docker compose exec -T db pg_dump -U mtg -d mtg_tracker -Fc -f "/tmp/$taskBackupName"
docker compose cp "db:/tmp/$taskBackupName" "tmp/$taskBackupName"
```

Confirm the dump was saved before continuing. For a managed PostgreSQL database,
use the provider's backup procedure. Coordinate upgrades to a shared database
with the team. Then run:

```powershell
uv run alembic upgrade head
uv run alembic current
```

The revision should be `002_adopt_schema_branch (head)`. Continue with the sample
import and startup commands in the README.

Revision `002_adopt_schema_branch` creates the new tables, seeds mana and rarity,
transfers the old records and relationships, and removes the retired plural
tables. Existing Scryfall UUIDs become card primary keys. Other legacy entity
IDs receive deterministic UUIDs. Main-deck and sideboard quantities, source
identifiers, timestamps, placements, and match outcomes are retained. Match
players and their game scores are swapped together when canonical order requires
it. Existing stored match results are treated as completed matches.

The transfer and DDL are one PostgreSQL transaction. Data that violates the new
design causes the entire migration to roll back, leaving the old tables intact.
Examples include duplicate player/card names ignoring case, a deck title over
64 characters, a player name over 64 characters, a format name over 16 characters,
and a match winner inconsistent with its game scores. Fix such records explicitly
instead of truncating or guessing their meaning.

Automatic downgrade is refused because the old design cannot preserve all the
new catalog data. Recovery uses the pre-upgrade backup. The migration requires
a live PostgreSQL connection; SQLite and offline SQL generation are unsupported
for this data-transfer revision.

For a fresh application database, use Alembic followed by the existing sample
import command in the README. `database/queries/schema/mtg_schema.pgsql` is an
alternative, empty-database-only initializer for database work. It does not
manage Alembic history; do not run both initialization paths on the same database.

## Verification

For local PostgreSQL tests, create a dedicated test database once (omit `createdb`
if it already exists). These PowerShell commands use the port from Docker:

```powershell
docker compose exec -T db createdb -U mtg mtg_tracker_test
$taskTestDbAddress = (docker compose port db 5432).Trim()
$env:TEST_DATABASE_URL = "postgresql+psycopg://mtg:mtg_local@$taskTestDbAddress/mtg_tracker_test"
uv run pytest
Remove-Item Env:TEST_DATABASE_URL
```

`uv run pytest` runs the API, importer, and constraint tests on SQLite with
foreign keys enabled. To exercise PostgreSQL as well, point `TEST_DATABASE_URL`
at a dedicated PostgreSQL test database, then run the same command. Tests create
and remove randomly named schemas; they do not replace application tables.
The existing GitHub checks now supply a PostgreSQL service and set this variable,
so migration checks will run in CI rather than being skipped there.

The PostgreSQL checks cover fresh migration, standalone initialization, ORM/DDL
agreement, transfer of populated legacy tables, and transaction rollback for
incompatible legacy records. The API and importer tests also run against
PostgreSQL when that variable is set.

This integration leaves the UI scope unchanged. Real MTG_decklistcache parsing,
match importing, and the unfinished card catalog importer remain separate work.
