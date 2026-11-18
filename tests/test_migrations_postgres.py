"""Real PostgreSQL DDL and legacy-data migration tests in disposable schemas.

Set TEST_DATABASE_URL to a dedicated local test database. No existing application
tables are changed: each test owns and removes only its randomly named schema.
"""

import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from mtg_tracker.core.config import get_settings
from mtg_tracker.db.base import Base
from mtg_tracker.models import Tournament
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DataError
from sqlalchemy.schema import CreateSchema, DropSchema

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def pg_schema(monkeypatch):
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL migration checks.")
    schema = f"migration_test_{uuid4().hex}"
    admin = create_engine(raw_url)
    with admin.begin() as conn:
        conn.execute(CreateSchema(schema))
    url = make_url(raw_url).update_query_dict({"options": f"-csearch_path={schema}"})
    monkeypatch.setenv("DATABASE_URL", url.render_as_string(hide_password=False))
    get_settings.cache_clear()
    engine = create_engine(url)
    try:
        yield engine, Config(str(ROOT / "alembic.ini"))
    finally:
        engine.dispose()
        get_settings.cache_clear()
        with admin.begin() as conn:
            conn.execute(DropSchema(schema, cascade=True))
        admin.dispose()


def seed_legacy(engine):
    # Frozen old-schema fixture. Include the same card in main and sideboard,
    # two players, entries, and a scored match to exercise relationship transfer.
    sql = """
    INSERT INTO tournaments
      (id, name, date, format, num_rounds, source_id, imported_at)
      VALUES (1, 'Legacy event', '2024-03-15', 'Standard', 3, 'legacy-event', CURRENT_TIMESTAMP);
    INSERT INTO players (id, name, source_id, imported_at) VALUES
      (1, 'Legacy Alice', 'alice', CURRENT_TIMESTAMP),
      (2, 'Legacy Bob', 'bob', CURRENT_TIMESTAMP);
    INSERT INTO cards (id, name, mana_cost, card_type, scryfall_id, imported_at) VALUES
      (1, 'Legacy card', '{R}', 'Instant', '00000000-0000-0000-0000-000000000042',
       CURRENT_TIMESTAMP);
    INSERT INTO decks (id, name, format, archetype, source_id, imported_at) VALUES
      (1, 'Legacy aggro', 'Standard', 'Aggro', 'aggro', CURRENT_TIMESTAMP),
      (2, 'Legacy control', 'Standard', 'Control', 'control', CURRENT_TIMESTAMP);
    INSERT INTO cards_in_decks (id, deck_id, card_id, zone, quantity) VALUES
      (1, 1, 1, 'main', 4), (2, 1, 1, 'sideboard', 2);
    INSERT INTO tournament_entries
      (id, tournament_id, player_id, deck_id, seed, final_placement) VALUES
      (10, 1, 1, 1, 1, 1), (11, 1, 2, 2, 2, 2);
    INSERT INTO tournament_matches
      (id, tournament_id, round_num, player_one_id, player_two_id, winner_id,
       player_one_wins, player_two_wins, draws) VALUES
       (20, 1, 1, 10, 11, 10, 2, 1, 0),
       (21, 1, 2, 11, 10, 10, 1, 2, 0),
       (22, 1, 3, 10, NULL, 10, 2, 0, 0),
       (23, 1, 4, 10, 11, NULL, 1, 1, 1);
    """
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)


def test_fresh_migration_matches_orm(pg_schema):
    engine, config = pg_schema
    command.upgrade(config, "head")
    with engine.connect() as conn:
        assert len(inspect(conn).get_table_names()) == 18  # 17 tables plus alembic_version.
        assert conn.execute(text("SELECT COUNT(*) FROM mana")).scalar_one() == 6
        assert conn.execute(text("SELECT COUNT(*) FROM rarity")).scalar_one() == 6
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


def test_standalone_sql_initializes_same_schema(pg_schema):
    engine, _ = pg_schema
    script = ROOT / "database/queries/schema/mtg_schema.pgsql"
    with engine.begin() as conn:
        conn.exec_driver_sql(script.read_text(encoding="utf-8"))
        assert set(inspect(conn).get_table_names()) == set(Base.metadata.tables)
        assert conn.execute(text("SELECT COUNT(*) FROM mana")).scalar_one() == 6


def test_existing_records_and_match_outcome_survive_upgrade(pg_schema):
    engine, config = pg_schema
    command.upgrade(config, "001_initial_schema")
    seed_legacy(engine)
    command.upgrade(config, "head")
    with engine.connect() as conn:
        assert "decks" not in inspect(conn).get_table_names()
        assert conn.execute(text("SELECT COUNT(*) FROM deck")).scalar_one() == 2
        assert conn.execute(text("SELECT COUNT(*) FROM player")).scalar_one() == 2
        assert conn.execute(text("SELECT COUNT(*) FROM tournamententry")).scalar_one() == 2
        card = conn.execute(text("SELECT pk_card, title, mana_cost FROM card")).one()
        assert card.pk_card == UUID("00000000-0000-0000-0000-000000000042")
        assert card.title == "Legacy card"
        assert card.mana_cost == "{R}"
        zones = conn.execute(text("SELECT zone, amount FROM card_in_deck ORDER BY zone")).all()
        assert zones == [("main", 4), ("sideboard", 2)]
        match = conn.execute(text("SELECT * FROM tournament_match WHERE round=1")).mappings().one()
        alice = conn.execute(
            text("SELECT pk_player FROM player WHERE source_id='alice'")
        ).scalar_one()
        assert match["playera"] > match["playerb"]
        winner = match["playera"] if match["wina"] > match["winb"] else match["playerb"]
        assert winner == alice
        assert match["done"] is True
        reverse = (
            conn.execute(text("SELECT * FROM tournament_match WHERE round=2")).mappings().one()
        )
        winner = reverse["playera"] if reverse["wina"] > reverse["winb"] else reverse["playerb"]
        assert winner == alice
        bye = conn.execute(text("SELECT * FROM tournament_match WHERE round=3")).mappings().one()
        assert bye["playerb"] is None and bye["winb"] == 0 and bye["draws"] == 0
        draw = conn.execute(text("SELECT * FROM tournament_match WHERE round=4")).mappings().one()
        assert draw["wina"] == draw["winb"] and draw["done"] is True
        assert (
            conn.execute(text("SELECT occurred FROM tournament")).scalar_one().isoformat()
            == "2024-03-15"
        )


@pytest.mark.parametrize("bad_data", ["long_title", "conflicting_winner"])
def test_incompatible_old_data_rolls_back_entire_upgrade(pg_schema, bad_data):
    engine, config = pg_schema
    command.upgrade(config, "001_initial_schema")
    seed_legacy(engine)
    with engine.begin() as conn:
        if bad_data == "long_title":
            conn.execute(text("UPDATE decks SET name = :name WHERE id = 1"), {"name": "x" * 65})
        else:
            conn.execute(text("UPDATE tournament_matches SET winner_id=11 WHERE id=20"))
    with pytest.raises(DataError if bad_data == "long_title" else ValueError):
        command.upgrade(config, "head")
    with engine.connect() as conn:
        tables = inspect(conn).get_table_names()
        assert "decks" in tables
        assert "deck" not in tables
        expected_name = "x" * 65 if bad_data == "long_title" else "Legacy aggro"
        assert conn.execute(text("SELECT name FROM decks WHERE id=1")).scalar_one() == expected_name
        assert (
            conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "001_initial_schema"
        )


def test_documented_matchup_sql_runs_on_postgresql(pg_schema):
    from conftest import seed_sample_data
    from sqlalchemy.orm import Session

    engine, config = pg_schema
    command.upgrade(config, "head")
    with Session(engine) as session:
        seeded = seed_sample_data(session)
        assert session.get(Tournament, seeded.tournaments["standard"]).format == "Standard"
    statement = text((ROOT / "database/queries/matchup_win_rates.sql").read_text(encoding="utf-8"))
    with engine.connect() as conn:
        rows = (
            conn.execute(
                statement,
                {
                    "format_filter": None,
                    "tournament_id": None,
                    "min_matches": 1,
                },
            )
            .mappings()
            .all()
        )
        assert sum(row["matches_played"] for row in rows) == 5
        standard = (
            conn.execute(
                statement,
                {
                    "format_filter": "Standard",
                    "tournament_id": seeded.tournaments["standard"],
                    "min_matches": 1,
                },
            )
            .mappings()
            .all()
        )
        assert sum(row["matches_played"] for row in standard) == 4
