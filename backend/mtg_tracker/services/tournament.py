"""Tournament and deck business logic; SQL lives in the repositories layer."""

import logging

from sqlalchemy.orm import Session

from mtg_tracker.models import Deck, Tournament
from mtg_tracker.repositories.decks import DeckRepository
from mtg_tracker.repositories.tournaments import TournamentRepository
from mtg_tracker.schemas.tournaments import TournamentSummary

logger = logging.getLogger(__name__)


class TournamentService:
    """Business logic for tournament operations."""

    @staticmethod
    def get_tournament_by_id(session: Session, tournament_id: int) -> Tournament | None:
        """Retrieve a tournament by ID."""
        return TournamentRepository.get_by_id(session, tournament_id)

    @staticmethod
    def get_tournament_by_source_id(session: Session, source_id: str) -> Tournament | None:
        """Retrieve a tournament by external source ID (for deduplication)."""
        return TournamentRepository.get_by_source_id(session, source_id)

    @staticmethod
    def list_tournaments(
        session: Session,
        format_filter: str | None = None,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Tournament]:
        """List tournaments, newest first, optionally filtered by format."""
        return TournamentRepository.list_all(session, format_filter, limit=limit, offset=offset)

    @staticmethod
    def count_tournaments(session: Session, format_filter: str | None = None) -> int:
        """Count tournaments matching the optional format filter."""
        return TournamentRepository.count(session, format_filter)

    @staticmethod
    def summarize(tournament: Tournament) -> TournamentSummary:
        """Build the API summary contract, including the entry count."""
        return TournamentSummary(
            id=tournament.id,
            name=tournament.name,
            format=tournament.format,
            date=tournament.date,
            location=tournament.location,
            num_rounds=tournament.num_rounds,
            player_count=len(tournament.entries),
        )

    @staticmethod
    def standings(session: Session, tournament_id: int) -> list[dict]:
        """Return entries ordered by final placement (nulls last)."""
        return TournamentRepository.standings(session, tournament_id)


class DeckService:
    """Business logic for deck operations."""

    @staticmethod
    def get_deck_by_id(session: Session, deck_id: int) -> Deck | None:
        """Retrieve a deck by ID."""
        return DeckRepository.get_by_id(session, deck_id)

    @staticmethod
    def get_deck_by_source_id(session: Session, source_id: str) -> Deck | None:
        """Retrieve a deck by external source ID."""
        return DeckRepository.get_by_source_id(session, source_id)

    @staticmethod
    def list_decks(
        session: Session,
        format_filter: str | None = None,
        archetype: str | None = None,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Deck]:
        """List decks by name, optionally filtered by format and archetype."""
        return DeckRepository.list_all(
            session, format_filter, archetype, limit=limit, offset=offset
        )

    @staticmethod
    def count_decks(
        session: Session,
        format_filter: str | None = None,
        archetype: str | None = None,
    ) -> int:
        """Count decks matching the optional filters."""
        return DeckRepository.count(session, format_filter, archetype)

    @staticmethod
    def deck_cards(session: Session, deck_id: int) -> list[dict]:
        """Return the deck's card slots (name, quantity, zone, mana cost)."""
        return DeckRepository.cards(session, deck_id)

    @staticmethod
    def deck_appearances(session: Session, deck_id: int) -> list[dict]:
        """Return the tournaments a deck appeared in, most recent first."""
        return DeckRepository.appearances(session, deck_id)

    @staticmethod
    def calculate_deck_size(session: Session, deck_id: int) -> int:
        """Calculate the total number of cards in a deck's main deck."""
        from mtg_tracker.models import CardInDeck

        result = (
            session.query(CardInDeck)
            .filter_by(deck_id=deck_id, zone="main")
            .with_entities(CardInDeck.quantity)
        )
        return sum(qty[0] for qty in result)

    @staticmethod
    def calculate_sideboard_size(session: Session, deck_id: int) -> int:
        """Calculate the total number of cards in a deck's sideboard."""
        from mtg_tracker.models import CardInDeck

        result = (
            session.query(CardInDeck)
            .filter_by(deck_id=deck_id, zone="sideboard")
            .with_entities(CardInDeck.quantity)
        )
        return sum(qty[0] for qty in result)

    @staticmethod
    def validate_deck_legality(
        session: Session, deck_id: int, format_name: str
    ) -> tuple[bool, list[str]]:
        """
        Validate deck legality for a given format.
        Returns (is_legal, errors).

        Currently implements basic checks:
        - Deck size should be at least 60 cards for most formats
        - Sideboard should be at most 15 cards
        - Card copies should not exceed 4 per card (with some exceptions)
        """
        from mtg_tracker.models import Card, CardInDeck

        errors = []
        deck = session.query(Deck).filter_by(id=deck_id).first()
        if not deck:
            return False, ["Deck not found"]

        main_size = DeckService.calculate_deck_size(session, deck_id)
        sideboard_size = DeckService.calculate_sideboard_size(session, deck_id)

        # Basic format-agnostic checks
        if main_size < 60:
            errors.append(f"Deck size is {main_size}, must be at least 60")
        if sideboard_size > 15:
            errors.append(f"Sideboard size is {sideboard_size}, must be at most 15")

        # Check copy limits
        card_counts = (
            session.query(Card.name, CardInDeck.quantity)
            .join(CardInDeck, CardInDeck.card_id == Card.id)
            .filter(CardInDeck.deck_id == deck_id, CardInDeck.zone == "main")
            .all()
        )

        for card_name, quantity in card_counts:
            # Some cards are allowed up to 5+ copies (e.g., "Relentless Rats")
            # For now, enforce 4 as default
            if quantity > 4 and card_name not in ["Relentless Rats", "Seven Dwarfs"]:
                errors.append(f"Card '{card_name}' has {quantity} copies, maximum is 4")

        is_legal = len(errors) == 0
        return is_legal, errors
