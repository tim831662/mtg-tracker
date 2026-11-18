"""The selected 17-table schema, registered for ORM and Alembic discovery."""

from mtg_tracker.models.catalog import (
    Artist,
    ArtistWorkedOnCard,
    Card,
    CardIsType,
    CardManaCost,
    Format,
    FormatRestriction,
    Keyword,
    Mana,
    Rarity,
    Subtype,
)
from mtg_tracker.models.tournament import (
    CardInDeck,
    Deck,
    Player,
    Tournament,
    TournamentEntry,
    TournamentMatch,
)

__all__ = [
    "Artist",
    "ArtistWorkedOnCard",
    "Card",
    "CardInDeck",
    "CardIsType",
    "CardManaCost",
    "Deck",
    "Format",
    "FormatRestriction",
    "Keyword",
    "Mana",
    "Player",
    "Rarity",
    "Subtype",
    "Tournament",
    "TournamentEntry",
    "TournamentMatch",
]
