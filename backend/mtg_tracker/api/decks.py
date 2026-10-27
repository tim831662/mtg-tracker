"""Deck browser and deck detail API placeholders."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("", responses={501: {"description": "Not implemented"}})
def list_decks() -> None:
    raise HTTPException(status_code=501, detail="Deck search is not implemented yet.")


@router.get("/{deck_id}", responses={501: {"description": "Not implemented"}})
def get_deck(deck_id: UUID) -> None:
    raise HTTPException(status_code=501, detail="Deck details are not implemented yet.")
