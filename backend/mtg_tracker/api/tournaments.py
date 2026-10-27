"""Tournament and standings API placeholders."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.get("", responses={501: {"description": "Not implemented"}})
def list_tournaments() -> None:
    raise HTTPException(status_code=501, detail="Tournament browsing is not implemented yet.")
