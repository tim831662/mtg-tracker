"""Application composition; feature logic belongs in the dedicated modules."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from mtg_tracker.api.router import router as api_router
from mtg_tracker.core.config import get_settings
from mtg_tracker.web.routes import WEB_DIR
from mtg_tracker.web.routes import router as web_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
    app.include_router(api_router, prefix="/api")
    app.include_router(web_router)
    return app


app = create_app()
