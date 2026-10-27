"""Compose API routes as features are added."""

from fastapi import APIRouter

from mtg_tracker.api import analytics, decks, tournaments

router = APIRouter()
router.include_router(decks.router)
router.include_router(tournaments.router)
router.include_router(analytics.router)


@router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Application liveness only; does not check the database or data sources."""
    return {"status": "ok"}
