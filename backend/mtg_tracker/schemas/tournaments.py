"""Response contracts for tournament endpoints. Field names are the frontend API contract."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TournamentSummary(BaseModel):
    """A tournament as it appears in list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    format: str
    date: datetime
    location: str | None = None
    num_rounds: int
    player_count: int = 0


class TournamentStanding(BaseModel):
    """One player's entry in a tournament, ordered by final placement."""

    entry_id: int
    player_id: int
    player_name: str
    deck_id: int
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
