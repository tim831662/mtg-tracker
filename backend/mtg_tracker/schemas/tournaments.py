"""Response contracts for tournament endpoints. Field names are the frontend API contract."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TournamentSummary(BaseModel):
    """A tournament as it appears in list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    format: str
    date: date
    location: str | None = None
    num_rounds: int
    player_count: int = 0


class TournamentStanding(BaseModel):
    """One player's entry in a tournament, ordered by final placement."""

    tournament_id: UUID
    player_id: UUID
    player_name: str
    deck_id: UUID
    deck_name: str
    archetype: str | None = None
    seed: int | None = None
    final_placement: int | None = None


class TournamentDetail(TournamentSummary):
    """A tournament with its final standings."""

    standings: list[TournamentStanding]


class TournamentListResponse(BaseModel):
    """Paginated tournament list envelope shared by all list endpoints."""

    items: list[TournamentSummary]
    total: int
    limit: int
    offset: int
