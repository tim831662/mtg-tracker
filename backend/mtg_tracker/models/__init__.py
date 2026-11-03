"""Define relational models here and import them here for Alembic discovery.

Planned: cards, mana types/costs, card types, formats/restrictions, decks/deck cards,
players, tournaments, entries, and matches. See docs/database-design.md first.
"""

from mtg_tracker.models.tournament import (
    Card,
    CardInDeck,
    Deck,
    Player,
    Tournament,
    TournamentEntry,
    TournamentMatch,
)

__all__ = [
    "Tournament",
    "Player",
    "Deck",
    "Card",
    "CardInDeck",
    "TournamentEntry",
    "TournamentMatch",
]
