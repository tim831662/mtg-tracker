"""Adopt the selected UUID schema and migrate the seven legacy tables.

Revision ID: 002_adopt_schema_branch
Revises: 001_initial_schema

DDL and data transfer run in the same PostgreSQL transaction. If old data cannot
satisfy the new constraints, the upgrade fails without removing the old tables.
"""

from datetime import UTC
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import sqlalchemy as sa
from alembic import op

revision = "002_adopt_schema_branch"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None

LEGACY_TABLES = (
    "tournaments",
    "players",
    "cards",
    "decks",
    "cards_in_decks",
    "tournament_entries",
    "tournament_matches",
)


def legacy_uuid(table, value):
    return uuid5(NAMESPACE_URL, f"mtg-tracker:legacy:{table}:{value}")


def upgrade():
    if op.get_context().as_sql:
        raise RuntimeError("This data migration requires an online PostgreSQL connection.")
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        raise RuntimeError("The selected schema migration requires PostgreSQL.")
    old = {
        table: list(conn.execute(sa.text(f'SELECT * FROM "{table}"')).mappings())
        for table in LEGACY_TABLES
    }
    ddl = Path(__file__).resolve().parents[1] / "sql/002_schema_branch.sql"
    conn.exec_driver_sql(ddl.read_text(encoding="utf-8"))
    metadata = sa.MetaData()
    names = [
        "player",
        "deck",
        "card",
        "card_in_deck",
        "format",
        "tournament",
        "tournamententry",
        "tournament_match",
    ]
    metadata.reflect(bind=conn, only=names)

    def insert(table, rows):
        if rows:
            conn.execute(metadata.tables[table].insert(), rows)

    def timestamp(row):
        value = row["imported_at"]
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value

    formats = {}
    for row in old["tournaments"] + old["decks"]:
        name = row["format"].strip() or "Unknown"
        key = name.upper()
        formats.setdefault(key, {"pk_format": legacy_uuid("format", key), "name_format": name})
    insert("format", list(formats.values()))
    players = {row["id"]: legacy_uuid("players", row["id"]) for row in old["players"]}
    decks = {row["id"]: legacy_uuid("decks", row["id"]) for row in old["decks"]}
    tournaments = {row["id"]: legacy_uuid("tournaments", row["id"]) for row in old["tournaments"]}
    cards = {
        row["id"]: UUID(row["scryfall_id"])
        if row["scryfall_id"]
        else legacy_uuid("cards", row["id"])
        for row in old["cards"]
    }
    insert(
        "player",
        [
            {
                "pk_player": players[row["id"]],
                "name_real": row["name"],
                "source_id": row["source_id"],
                "imported_at": timestamp(row),
            }
            for row in old["players"]
        ],
    )
    insert(
        "card",
        [
            {
                "pk_card": cards[row["id"]],
                "title": row["name"],
                "mana_cost": row["mana_cost"],
                "type_line": row["card_type"],
                "imported_at": timestamp(row),
            }
            for row in old["cards"]
        ],
    )
    insert(
        "deck",
        [
            {
                "pk_deck": decks[row["id"]],
                "title": row["name"],
                "format": formats[(row["format"].strip() or "Unknown").upper()]["pk_format"],
                "archetype": row["archetype"],
                "source_id": row["source_id"],
                "imported_at": timestamp(row),
            }
            for row in old["decks"]
        ],
    )
    insert(
        "tournament",
        [
            {
                "pk_tournament": tournaments[row["id"]],
                "id": row["source_id"],
                "name": row["name"],
                "loc": row["location"],
                "occurred": row["date"].date(),
                "format": formats[(row["format"].strip() or "Unknown").upper()]["pk_format"],
                "num_rounds": row["num_rounds"],
                "source_url": row["source_url"],
                "imported_at": timestamp(row),
            }
            for row in old["tournaments"]
        ],
    )
    insert(
        "card_in_deck",
        [
            {
                "deck": decks[row["deck_id"]],
                "card": cards[row["card_id"]],
                "zone": row["zone"],
                "amount": row["quantity"],
            }
            for row in old["cards_in_decks"]
        ],
    )
    insert(
        "tournamententry",
        [
            {
                "player": players[row["player_id"]],
                "tournament": tournaments[row["tournament_id"]],
                "deck": decks[row["deck_id"]],
                "placement": row["final_placement"],
                "seed": row["seed"],
            }
            for row in old["tournament_entries"]
        ],
    )
    entries = {row["id"]: row for row in old["tournament_entries"]}
    matches = []
    for row in old["tournament_matches"]:
        first = entries[row["player_one_id"]]
        second = entries[row["player_two_id"]] if row["player_two_id"] is not None else None
        if first["tournament_id"] != row["tournament_id"] or (
            second is not None and second["tournament_id"] != row["tournament_id"]
        ):
            raise ValueError(f"Legacy match {row['id']} references an entry in another tournament.")
        a, b = players[first["player_id"]], players[second["player_id"]] if second else None
        wins_a, wins_b = row["player_one_wins"], row["player_two_wins"]
        expected = (
            row["player_one_id"]
            if wins_a > wins_b
            else (row["player_two_id"] if wins_b > wins_a else None)
        )
        if row["winner_id"] != expected:
            raise ValueError(f"Legacy match {row['id']} winner conflicts with its game scores.")
        if b is not None and a < b:
            a, b, wins_a, wins_b = b, a, wins_b, wins_a
        matches.append(
            {
                "pk_match": legacy_uuid("tournament_matches", row["id"]),
                "tournament": tournaments[row["tournament_id"]],
                "round": row["round_num"],
                "playera": a,
                "playerb": b,
                "wina": wins_a,
                "winb": wins_b,
                "draws": row["draws"],
                "done": True,
            }
        )
    insert("tournament_match", matches)
    for table in reversed(LEGACY_TABLES):
        op.drop_table(table)


def downgrade():
    raise RuntimeError(
        "The UUID schema cannot be losslessly converted back to the old schema. "
        "Restore the pre-upgrade backup instead of discarding catalog data."
    )
