"""API contract tests for decks, tournaments, and matchup analytics."""

import pytest


def test_list_decks(client, seeded):
    body = client.get("/api/decks").json()
    assert body["total"] == 4
    assert len(body["items"]) == 4
    assert {"id", "name", "format", "archetype"} <= set(body["items"][0])


def test_list_decks_format_filter(client, seeded):
    body = client.get("/api/decks", params={"format": "Standard"}).json()
    assert body["total"] == 2
    assert all(deck["format"] == "Standard" for deck in body["items"])


def test_list_decks_archetype_filter(client, seeded):
    body = client.get("/api/decks", params={"archetype": "Aggro"}).json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Mono Red"


def test_list_decks_pagination(client, seeded):
    body = client.get("/api/decks", params={"limit": 1, "offset": 2}).json()
    assert body["total"] == 4
    assert len(body["items"]) == 1
    assert body["limit"] == 1
    assert body["offset"] == 2


def test_deck_detail(client, seeded):
    response = client.get(f"/api/decks/{seeded.decks['mono_red']}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Mono Red"
    assert body["format"] == "Standard"
    assert body["maindeck_size"] == 4
    assert body["sideboard_size"] == 2
    assert {card["zone"] for card in body["cards"]} == {"main", "sideboard"}
    assert body["appearances"][0]["player_name"] == "Alice"
    assert body["appearances"][0]["final_placement"] == 2


def test_deck_detail_not_found(client, seeded):
    response = client.get("/api/decks/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_tournaments(client, seeded):
    body = client.get("/api/tournaments").json()
    assert body["total"] == 2
    counts = {item["name"]: item["player_count"] for item in body["items"]}
    assert counts["Standard Showdown"] == 4
    assert counts["Pioneer Preliminary"] == 2
    # Newest first.
    assert body["items"][0]["name"] == "Pioneer Preliminary"


def test_list_tournaments_format_filter(client, seeded):
    body = client.get("/api/tournaments", params={"format": "Pioneer"}).json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Pioneer Preliminary"


def test_tournament_detail_standings(client, seeded):
    response = client.get(f"/api/tournaments/{seeded.tournaments['standard']}")
    assert response.status_code == 200
    body = response.json()
    assert body["player_count"] == 4
    placements = [standing["final_placement"] for standing in body["standings"]]
    assert placements == sorted(placements)
    assert body["standings"][0]["player_name"] == "Bob"
    assert body["standings"][0]["deck_name"] == "Azorius Control"


def test_tournament_detail_not_found(client, seeded):
    assert client.get("/api/tournaments/999").status_code == 404


def test_analytics_index(client, seeded):
    body = client.get("/api/analytics").json()
    assert body == {"endpoints": ["matchups"]}


def test_matchup_win_rates(client, seeded):
    body = client.get("/api/analytics/matchups").json()
    rows = {(row["archetype_a"], row["archetype_b"]): row for row in body["items"]}

    aggro_control = rows[("Aggro", "Control")]
    assert aggro_control["matches_played"] == 3
    assert aggro_control["wins_a"] == 2
    assert aggro_control["wins_b"] == 1
    assert aggro_control["draws"] == 0
    assert aggro_control["win_rate_a"] == pytest.approx(2 / 3, abs=1e-3)

    control_aggro = rows[("Control", "Aggro")]
    assert control_aggro["matches_played"] == 1
    assert control_aggro["draws"] == 1
    assert control_aggro["win_rate_a"] == 0.0

    # The bye is excluded; the Pioneer pair is included.
    assert len(body["items"]) == 3


def test_matchup_win_rates_format_filter(client, seeded):
    body = client.get("/api/analytics/matchups", params={"format": "Pioneer"}).json()
    assert len(body["items"]) == 1
    row = body["items"][0]
    assert (row["archetype_a"], row["archetype_b"]) == ("Midrange", "Tempo")
    assert row["wins_b"] == 1
    assert row["win_rate_a"] == 0.0


def test_matchup_win_rates_tournament_filter(client, seeded):
    body = client.get(
        "/api/analytics/matchups", params={"tournament_id": seeded.tournaments["standard"]}
    ).json()
    assert len(body["items"]) == 2


def test_matchup_win_rates_min_matches(client, seeded):
    body = client.get("/api/analytics/matchups", params={"min_matches": 2}).json()
    assert [row["matches_played"] for row in body["items"]] == [3]
