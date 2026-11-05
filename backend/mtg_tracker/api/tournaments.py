"""Tournament browsing and standings API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from mtg_tracker.db.session import get_session
from mtg_tracker.schemas.tournaments import TournamentDetail, TournamentListResponse
from mtg_tracker.services import TournamentService

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=TournamentListResponse)
def list_tournaments(
    session: SessionDep,
    format: Annotated[str | None, Query(description="Filter by format, e.g. Standard")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
) -> TournamentListResponse:
    """List tournaments, newest first, with optional format filter and pagination."""
    tournaments = TournamentService.list_tournaments(
        session, format_filter=format, limit=limit, offset=offset
    )
    total = TournamentService.count_tournaments(session, format_filter=format)
    return TournamentListResponse(
        items=[TournamentService.summarize(tournament) for tournament in tournaments],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{tournament_id}", response_model=TournamentDetail)
def get_tournament(
    session: SessionDep,
    tournament_id: Annotated[int, Path(description="Numeric tournament ID")],
) -> TournamentDetail:
    """Retrieve one tournament with its final standings."""
    tournament = TournamentService.get_tournament_by_id(session, tournament_id)
    if tournament is None:
        raise HTTPException(status_code=404, detail=f"Tournament {tournament_id} not found.")

    summary = TournamentService.summarize(tournament)
    return TournamentDetail(
        **summary.model_dump(),
        standings=TournamentService.standings(session, tournament_id),
    )
