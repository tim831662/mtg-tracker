"""Lazy session setup keeps the application shell independent of PostgreSQL."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mtg_tracker.core.config import get_settings


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    engine = create_engine(get_settings().database_url.get_secret_value(), pool_pre_ping=True)
    return sessionmaker(bind=engine)


def get_session() -> Iterator[Session]:
    """Future routes can inject this dependency; services own transaction boundaries."""
    with get_session_factory()() as session:
        yield session
