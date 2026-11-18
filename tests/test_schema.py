"""Schema invariants exercised on SQLite and, with TEST_DATABASE_URL, PostgreSQL."""

from uuid import UUID, uuid4

import pytest
from mtg_tracker.importers.tournaments import TournamentImporter
from mtg_tracker.models import (
    CardInDeck,
    CardManaCost,
    Format,
    FormatRestriction,
    TournamentEntry,
    TournamentMatch,
)
from mtg_tracker.services import DeckService, MatchupService
from sqlalchemy.exc import IntegrityError


@pytest.mark.parametrize("quantity,zone", [(0, "main"), (-1, "main"), (1, "unknown")])
def test_deck_card_constraints(session, seeded, quantity, zone):
    session.add(
        CardInDeck(
            deck_id=seeded.decks["mono_red"],
            card_id=seeded.cards["Counterspell"],
            quantity=quantity,
            zone=zone,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_same_card_can_be_in_both_zones(session, seeded):
    session.add(
        CardInDeck(
            deck_id=seeded.decks["mono_red"],
            card_id=seeded.cards["Lightning Bolt"],
            quantity=1,
            zone="sideboard",
        )
    )
    session.commit()
    assert (
        session.query(CardInDeck)
        .filter_by(
            deck_id=seeded.decks["mono_red"],
            card_id=seeded.cards["Lightning Bolt"],
        )
        .count()
        == 2
    )


def test_foreign_keys_are_enforced(session, seeded):
    session.add(
        CardInDeck(
            deck_id=seeded.decks["mono_red"],
            card_id=uuid4(),
            quantity=1,
            zone="main",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_entry_uses_player_and_tournament_composite_key(session, seeded):
    session.add(
        TournamentEntry(
            player_id=seeded.players["Alice"],
            tournament_id=seeded.tournaments["standard"],
            deck_id=seeded.decks["mono_red"],
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_match_players_must_enter_that_tournament(session, seeded):
    session.add(
        TournamentMatch(
            tournament_id=seeded.tournaments["standard"],
            round_num=10,
            player_one_id=seeded.players["Erin"],
            player_two_id=seeded.players["Frank"],
            player_one_wins=2,
            done=True,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_match_order_is_canonical(session, seeded):
    session.add(
        TournamentMatch(
            tournament_id=seeded.tournaments["standard"],
            round_num=10,
            player_one_id=seeded.players["Bob"],
            player_two_id=seeded.players["Alice"],
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_incomplete_matches_are_not_counted(session, seeded):
    session.add(
        TournamentMatch(
            tournament_id=seeded.tournaments["standard"],
            round_num=10,
            player_one_id=seeded.players["Alice"],
            player_two_id=seeded.players["Bob"],
            done=False,
        )
    )
    session.commit()
    rows = MatchupService.matchup_win_rates(session, format_filter="Standard")
    assert sum(row["matches_played"] for row in rows) == 4


@pytest.mark.parametrize("mask,amount", [(0, 1), (64, 1), (1, 0)])
def test_mana_cost_constraints(session, seeded, mask, amount):
    session.add(CardManaCost(card_id=seeded.cards["Lightning Bolt"], mana_type=mask, amount=amount))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_format_restriction_must_be_nonnegative(session, seeded):
    standard = session.query(Format).filter_by(name="Standard").one()
    session.add(
        FormatRestriction(
            format_id=standard.id,
            card_id=seeded.cards["Lightning Bolt"],
            maximum=-1,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_existing_json_import_works_and_is_repeatable(session):
    from pathlib import Path

    from mtg_tracker.models import Card, Deck, Player, Tournament

    source = Path(__file__).resolve().parents[1] / "database/seeds/sample_tournament_data.json"
    TournamentImporter(session).run(source)
    TournamentImporter(session).run(source)
    assert session.query(Format).count() == 2
    assert session.query(Tournament).count() == 2
    assert session.query(Player).count() == 6
    assert session.query(Deck).count() == 6
    assert session.query(Card).count() == 8
    assert session.query(TournamentEntry).count() == 7
    assert isinstance(session.query(Deck).first().id, UUID)
    assert session.query(TournamentMatch).count() == 0  # Still intentionally unfinished.


def test_basic_deck_validation_uses_normalized_format_rules(session, seeded):
    standard = session.query(Format).filter_by(name="Standard").one()
    standard.minimum_size = 4
    standard.copy_limit = 0  # The schema design uses zero for unlimited copies.
    session.flush()
    valid, errors = DeckService.validate_deck_legality(
        session, seeded.decks["mono_red"], "Standard"
    )
    assert valid, errors
    standard.copy_limit = 3
    session.flush()
    valid, errors = DeckService.validate_deck_legality(
        session, seeded.decks["mono_red"], "Standard"
    )
    assert not valid
    assert any("maximum is 3" in error for error in errors)
