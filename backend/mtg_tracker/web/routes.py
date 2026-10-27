"""Navigation targets matching the four screens in the class project brief."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

WEB_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=WEB_DIR / "templates")
router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/decks", response_class=HTMLResponse)
def decks(request: Request):
    return templates.TemplateResponse(request=request, name="decks.html")


@router.get("/decks/preview", response_class=HTMLResponse)
def deck_preview(request: Request):
    """Static layout placeholder; real deck IDs and lookup will be added later."""
    return templates.TemplateResponse(request=request, name="deck_detail.html")


@router.get("/tournaments", response_class=HTMLResponse)
def tournaments(request: Request):
    return templates.TemplateResponse(request=request, name="tournaments.html")
