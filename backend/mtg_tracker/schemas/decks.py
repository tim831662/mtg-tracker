"""Response contracts for deck endpoints. Field names are the frontend API contract."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeckSummary(BaseModel):
    """A deck as it appears in list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    format: str
    archetype: str | None = None


class DeckCard(BaseModel):
    """One card slot (card, quantity, and zone) within a decklist."""

    name: str
    quantity: int
    zone: str
    mana_cost: str | None = None


class DeckAppearance(BaseModel):
    """One tournament appearance of a deck."""

    tournament_id: int
    tournament_name: str
    tournament_date: datetime
    player_id: int
    player_name: str
    final_placement: int | None = None


class DeckDetail(DeckSummary):
    """A deck with its card list and tournament appearances."""

    cards: list[DeckCard]
    maindeck_size: int
    sideboard_size: int
    appearances: list[DeckAppearance]


class DeckListResponse(BaseModel):
    """Paginated deck list envelope shared by all list endpoints."""

    items: list[DeckSummary]
    total: int
    limit: int
    offset: int
