"""Metagame analytics API: matchup win rates."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from mtg_tracker.db.session import get_session
from mtg_tracker.schemas.analytics import MatchupWinRateList
from mtg_tracker.services import MatchupService

router = APIRouter(prefix="/analytics", tags=["analytics"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("")
def analytics_index() -> dict[str, list[str]]:
    """List the available analytics resources."""
    return {"endpoints": ["matchups"]}


@router.get("/matchups", response_model=MatchupWinRateList)
def matchup_win_rates(
    session: SessionDep,
    format: Annotated[str | None, Query(description="Filter by format, e.g. Standard")] = None,
    tournament_id: Annotated[int | None, Query(description="Restrict to one tournament")] = None,
    min_matches: Annotated[
        int, Query(ge=1, description="Exclude archetype pairs with fewer matches")
    ] = 1,
) -> MatchupWinRateList:
    """Matchup win rates by archetype pair, most-played pairs first.

    Byes are excluded; drawn matches count toward matches_played but toward
    neither side's wins. Rows are directional (archetype_a was player one).
    """
    items = MatchupService.matchup_win_rates(
        session, format_filter=format, tournament_id=tournament_id, min_matches=min_matches
    )
    return MatchupWinRateList(items=items)
