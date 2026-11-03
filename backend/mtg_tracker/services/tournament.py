"""Tournament data validation and business logic services."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from mtg_tracker.models import Deck, Tournament

logger = logging.getLogger(__name__)


class TournamentService:
    """Business logic for tournament operations."""

    @staticmethod
    def get_tournament_by_id(session: Session, tournament_id: int) -> Optional[Tournament]:
        """Retrieve a tournament by ID."""
        return session.query(Tournament).filter_by(id=tournament_id).first()

    @staticmethod
    def get_tournament_by_source_id(session: Session, source_id: str) -> Optional[Tournament]:
        """Retrieve a tournament by external source ID (for deduplication)."""
        return session.query(Tournament).filter_by(source_id=source_id).first()

    @staticmethod
    def list_tournaments(session: Session, format_filter: Optional[str] = None) -> list[Tournament]:
        """List tournaments, optionally filtered by format."""
        query = session.query(Tournament).order_by(Tournament.date.desc())
        if format_filter:
            query = query.filter_by(format=format_filter)
        return query.all()


class DeckService:
    """Business logic for deck operations."""

    @staticmethod
    def get_deck_by_id(session: Session, deck_id: int) -> Optional[Deck]:
        """Retrieve a deck by ID."""
        return session.query(Deck).filter_by(id=deck_id).first()

    @staticmethod
    def get_deck_by_source_id(session: Session, source_id: str) -> Optional[Deck]:
        """Retrieve a deck by external source ID."""
        return session.query(Deck).filter_by(source_id=source_id).first()

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
