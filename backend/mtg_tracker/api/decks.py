"""Deck browsing and deck detail API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from mtg_tracker.db.session import get_session
from mtg_tracker.schemas.decks import DeckDetail, DeckListResponse, DeckSummary
from mtg_tracker.services import DeckService

router = APIRouter(prefix="/decks", tags=["decks"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=DeckListResponse)
def list_decks(
    session: SessionDep,
    format: Annotated[str | None, Query(description="Filter by format, e.g. Pioneer")] = None,
    archetype: Annotated[str | None, Query(description="Filter by archetype, e.g. Control")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
) -> DeckListResponse:
    """List decks with optional format and archetype filters and pagination."""
    decks = DeckService.list_decks(
        session, format_filter=format, archetype=archetype, limit=limit, offset=offset
    )
    total = DeckService.count_decks(session, format_filter=format, archetype=archetype)
    return DeckListResponse(
        items=[DeckSummary.model_validate(deck) for deck in decks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{deck_id}", response_model=DeckDetail)
def get_deck(
    session: SessionDep,
    deck_id: Annotated[int, Path(description="Numeric deck ID")],
) -> DeckDetail:
    """Retrieve one deck with its card list and tournament appearances."""
    deck = DeckService.get_deck_by_id(session, deck_id)
    if deck is None:
        raise HTTPException(status_code=404, detail=f"Deck {deck_id} not found.")

    cards = DeckService.deck_cards(session, deck_id)
    appearances = DeckService.deck_appearances(session, deck_id)
    return DeckDetail(
        id=deck.id,
        name=deck.name,
        format=deck.format,
        archetype=deck.archetype,
        cards=cards,
        maindeck_size=sum(card["quantity"] for card in cards if card["zone"] == "main"),
        sideboard_size=sum(card["quantity"] for card in cards if card["zone"] == "sideboard"),
        appearances=appearances,
    )
