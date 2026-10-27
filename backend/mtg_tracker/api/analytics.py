"""Metagame analytics API placeholder."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", responses={501: {"description": "Not implemented"}})
def get_analytics() -> None:
    raise HTTPException(status_code=501, detail="Metagame analytics are not implemented yet.")
