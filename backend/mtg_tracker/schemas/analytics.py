"""Response contracts for metagame analytics endpoints."""

from pydantic import BaseModel


class MatchupWinRate(BaseModel):
    """Directional win rate of archetype A against archetype B.

    Byes are excluded. Drawn matches count toward matches_played but toward
    neither side's wins, so win_rate_a = wins_a / matches_played.
    """

    archetype_a: str
    archetype_b: str
    matches_played: int
    wins_a: int
    wins_b: int
    draws: int
    win_rate_a: float


class MatchupWinRateList(BaseModel):
    """Collection of matchup rows; ordering is matches_played descending."""

    items: list[MatchupWinRate]
