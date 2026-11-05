"""Public Pydantic request and response contracts for decks, events, and analytics."""

from mtg_tracker.schemas.analytics import MatchupWinRate, MatchupWinRateList
from mtg_tracker.schemas.decks import (
    DeckAppearance,
    DeckCard,
    DeckDetail,
    DeckListResponse,
    DeckSummary,
)
from mtg_tracker.schemas.tournaments import (
    TournamentDetail,
    TournamentListResponse,
    TournamentStanding,
    TournamentSummary,
)

__all__ = [
    "DeckAppearance",
    "DeckCard",
    "DeckDetail",
    "DeckListResponse",
    "DeckSummary",
    "MatchupWinRate",
    "MatchupWinRateList",
    "TournamentDetail",
    "TournamentListResponse",
    "TournamentStanding",
    "TournamentSummary",
]
