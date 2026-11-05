"""Shared fixtures: an isolated in-memory database and a seeded API client."""

from datetime import datetime
from types import SimpleNamespace

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
    Player,
    Tournament,
    TournamentEntry,
    TournamentMatch,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


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
    players = [Player(name=name) for name in ["Alice", "Bob", "Carol", "Dan", "Erin", "Frank"]]
    session.add_all(cards + players)
    session.flush()

    standard = Tournament(
        name="Standard Showdown",
        date=datetime(2024, 3, 15),
        format="Standard",
        location="Game Store",
        num_rounds=5,
    )
    pioneer = Tournament(
        name="Pioneer Preliminary",
        date=datetime(2024, 4, 20),
        format="Pioneer",
        location="Convention Center",
        num_rounds=6,
    )
    session.add_all([standard, pioneer])
    session.flush()

    mono_red = Deck(name="Mono Red", format="Standard", archetype="Aggro")
    control = Deck(name="Azorius Control", format="Standard", archetype="Control")
    rakdos = Deck(name="Rakdos Midrange", format="Pioneer", archetype="Midrange")
    phoenix = Deck(name="Izzet Phoenix", format="Pioneer", archetype="Tempo")
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
                tournament_id=standard.id,
                round_num=1,
                player_one_id=entries[0].id,
                player_two_id=entries[1].id,
                winner_id=entries[0].id,
                player_one_wins=2,
                player_two_wins=1,
            ),
            TournamentMatch(
                tournament_id=standard.id,
                round_num=1,
                player_one_id=entries[2].id,
                player_two_id=entries[3].id,
                winner_id=entries[2].id,
                player_one_wins=2,
                player_two_wins=0,
            ),
            TournamentMatch(
                tournament_id=standard.id,
                round_num=2,
                player_one_id=entries[0].id,
                player_two_id=entries[3].id,
                winner_id=entries[3].id,
                player_one_wins=1,
                player_two_wins=2,
            ),
            # Standard: Control as player one, drawn match.
            TournamentMatch(
                tournament_id=standard.id,
                round_num=2,
                player_one_id=entries[1].id,
                player_two_id=entries[2].id,
                winner_id=None,
                player_one_wins=1,
                player_two_wins=1,
                draws=1,
            ),
            # Standard: bye with no opponent; excluded from matchup analytics.
            TournamentMatch(
                tournament_id=standard.id,
                round_num=3,
                player_one_id=entries[0].id,
                player_two_id=None,
                winner_id=entries[0].id,
                player_one_wins=2,
                player_two_wins=0,
            ),
            # Pioneer: one Midrange vs Tempo match won by Tempo.
            TournamentMatch(
                tournament_id=pioneer.id,
                round_num=1,
                player_one_id=entries[4].id,
                player_two_id=entries[5].id,
                winner_id=entries[5].id,
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
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        yield db
    engine.dispose()


@pytest.fixture
def seeded(session: Session) -> SimpleNamespace:
    return seed_sample_data(session)


@pytest.fixture
def client(seeded: SimpleNamespace, session: Session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
