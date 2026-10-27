"""Smoke tests for the skeleton's usable shell and explicit unfinished features."""

import pytest
from fastapi.testclient import TestClient
from mtg_tracker.db.session import get_session_factory
from mtg_tracker.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


def test_shell_does_not_initialize_database(client):
    get_session_factory.cache_clear()
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200
    assert get_session_factory.cache_info().currsize == 0


@pytest.mark.parametrize("path", ["/", "/decks", "/decks/preview", "/tournaments"])
def test_screen_placeholders(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Project skeleton" in response.text


def test_static_styles_and_api_documentation(client):
    assert client.get("/static/styles.css").status_code == 200
    assert "/api/health" in client.get("/openapi.json").json()["paths"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/decks",
        "/api/decks/00000000-0000-0000-0000-000000000001",
        "/api/tournaments",
        "/api/analytics",
    ],
)
def test_feature_routes_are_explicit_stubs(client, path):
    response = client.get(path)
    assert response.status_code == 501
    assert "not implemented" in response.json()["detail"]
