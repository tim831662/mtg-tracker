"""Shared fixtures: an isolated in-memory database and a seeded API client."""

import os
from datetime import date
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from mtg_tracker import models  # noqa: F401 -- imported so create_all sees every mapping
from mtg_tracker.db.base import Base
from mtg_tracker.db.session import get_session
from mtg_tracker.main import create_app
from mtg_tracker.models import (
    Card,
    CardInDeck,
    Deck,
    Format,
    Player,
    Tournament,
    TournamentEntry,
    TournamentMatch,
)
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import CreateSchema, DropSchema


def seed_sample_data(session: Session) -> SimpleNamespace:
    """Seed a small, deterministic dataset and return the generated IDs.

    Expected matchup rows (see repositories/matchups.py for definitions):
      * (Aggro, Control): 3 matches, 2 wins for Aggro, 1 for Control
      * (Control, Aggro): 1 drawn match
      * (Midrange, Tempo): 1 match won by Tempo (Pioneer)
      * One bye (no opponent) that must be excluded everywhere.
    """
    cards = [
        Card(name="Lightning Bolt", mana_cost="{R}", card_type="Instant"),
        Card(name="Counterspell", mana_cost="{U}{U}", card_type="Instant"),
    ]
    players = [
        Player(id=UUID(int=value), name=name)
        for value, name in zip(
            [6, 4, 3, 2, 5, 1], ["Alice", "Bob", "Carol", "Dan", "Erin", "Frank"], strict=True
        )
    ]
    session.add_all(cards + players)
    session.flush()

    standard_format = Format(name="Standard")
    pioneer_format = Format(name="Pioneer")
    session.add_all([standard_format, pioneer_format])

    standard = Tournament(
        name="Standard Showdown",
        date=date(2024, 3, 15),
        format_rule=standard_format,
        location="Game Store",
        num_rounds=5,
    )
    pioneer = Tournament(
        name="Pioneer Preliminary",
        date=date(2024, 4, 20),
        format_rule=pioneer_format,
        location="Convention Center",
        num_rounds=6,
    )
    session.add_all([standard, pioneer])
    session.flush()

    mono_red = Deck(name="Mono Red", format_rule=standard_format, archetype="Aggro")
    control = Deck(name="Azorius Control", format_rule=standard_format, archetype="Control")
    rakdos = Deck(name="Rakdos Midrange", format_rule=pioneer_format, archetype="Midrange")
    phoenix = Deck(name="Izzet Phoenix", format_rule=pioneer_format, archetype="Tempo")
    session.add_all([mono_red, control, rakdos, phoenix])
    session.flush()

    session.add_all(
        [
            CardInDeck(deck_id=mono_red.id, card_id=cards[0].id, zone="main", quantity=4),
            CardInDeck(deck_id=mono_red.id, card_id=cards[1].id, zone="sideboard", quantity=2),
        ]
    )

    entries = [
        TournamentEntry(
            tournament_id=standard.id,
            player_id=players[0].id,
            deck_id=mono_red.id,
            seed=1,
            final_placement=2,
        ),
        TournamentEntry(
            tournament_id=standard.id,
            player_id=players[1].id,
            deck_id=control.id,
            seed=2,
            final_placement=1,
        ),
        TournamentEntry(
            tournament_id=standard.id,
            player_id=players[2].id,
            deck_id=mono_red.id,
            seed=3,
            final_placement=4,
        ),
        TournamentEntry(
            tournament_id=standard.id,
            player_id=players[3].id,
            deck_id=control.id,
            seed=4,
            final_placement=3,
        ),
        TournamentEntry(
            tournament_id=pioneer.id,
            player_id=players[4].id,
            deck_id=rakdos.id,
            seed=1,
            final_placement=2,
        ),
        TournamentEntry(
            tournament_id=pioneer.id,
            player_id=players[5].id,
            deck_id=phoenix.id,
            seed=2,
            final_placement=1,
        ),
    ]
    session.add_all(entries)
    session.flush()

    session.add_all(
        [
            # Standard: Aggro as player one against Control, three times.
            TournamentMatch(
                done=True,
                tournament_id=standard.id,
                round_num=1,
                player_one_id=players[0].id,
                player_two_id=players[1].id,
                player_one_wins=2,
                player_two_wins=1,
            ),
            TournamentMatch(
                done=True,
                tournament_id=standard.id,
                round_num=1,
                player_one_id=players[2].id,
                player_two_id=players[3].id,
                player_one_wins=2,
                player_two_wins=0,
            ),
            TournamentMatch(
                done=True,
                tournament_id=standard.id,
                round_num=2,
                player_one_id=players[0].id,
                player_two_id=players[3].id,
                player_one_wins=1,
                player_two_wins=2,
            ),
            # Standard: Control as player one, drawn match.
            TournamentMatch(
                done=True,
                tournament_id=standard.id,
                round_num=2,
                player_one_id=players[1].id,
                player_two_id=players[2].id,
                player_one_wins=1,
                player_two_wins=1,
                draws=1,
            ),
            # Standard: bye with no opponent; excluded from matchup analytics.
            TournamentMatch(
                done=True,
                tournament_id=standard.id,
                round_num=3,
                player_one_id=players[0].id,
                player_two_id=None,
                player_one_wins=2,
                player_two_wins=0,
            ),
            # Pioneer: one Midrange vs Tempo match won by Tempo.
            TournamentMatch(
                done=True,
                tournament_id=pioneer.id,
                round_num=1,
                player_one_id=players[4].id,
                player_two_id=players[5].id,
                player_one_wins=1,
                player_two_wins=2,
            ),
        ]
    )
    session.commit()

    return SimpleNamespace(
        cards={card.name: card.id for card in cards},
        players={player.name: player.id for player in players},
        tournaments={"standard": standard.id, "pioneer": pioneer.id},
        decks={
            "mono_red": mono_red.id,
            "control": control.id,
            "rakdos": rakdos.id,
            "phoenix": phoenix.id,
        },
    )


@pytest.fixture
def session() -> Session:
    url = os.environ.get("TEST_DATABASE_URL")
    schema = f"test_{uuid4().hex}"
    admin = None
    if url:
        admin = create_engine(url)
        with admin.begin() as conn:
            conn.execute(CreateSchema(schema))
        engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

    try:
        Base.metadata.create_all(engine)
        with sessionmaker(bind=engine)() as db:
            yield db
    finally:
        engine.dispose()
        if admin is not None:
            with admin.begin() as conn:
                conn.execute(DropSchema(schema, cascade=True))
            admin.dispose()


@pytest.fixture
def seeded(session: Session) -> SimpleNamespace:
    return seed_sample_data(session)


@pytest.fixture
def client(seeded: SimpleNamespace, session: Session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
