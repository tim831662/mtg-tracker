"""Keep the documented sample import compatible with PostgreSQL's UUID-sized column."""

import json
from pathlib import Path
from uuid import UUID


def test_sample_scryfall_ids_are_canonical_uuids():
    path = Path(__file__).resolve().parents[1] / "database/seeds/sample_tournament_data.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for card in data["cards"]:
        if value := card.get("scryfall_id"):
            assert value == str(UUID(value)), card["name"]
