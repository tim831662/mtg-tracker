"""Entry point for importing tournament data from JSON files."""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from mtg_tracker.db.session import get_session_factory
from mtg_tracker.models import Card, CardInDeck, Deck, Player, Tournament, TournamentEntry

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class TournamentImporter:
    """Imports tournament data from JSON format into PostgreSQL."""

    def __init__(self, session: Session):
        """Initialize importer with database session."""
        self.session = session
        self.tournament_map = {}  # Maps source IDs to Tournament objects
        self.player_map = {}  # Maps source IDs to Player objects
        self.card_map = {}  # Maps source IDs to Card objects
        self.deck_map = {}  # Maps source IDs to Deck objects
        self.entry_map = {}  # Maps (tournament_id, player_id) to TournamentEntry objects

    def load_json(self, file_path: Path) -> dict:
        """Load tournament data from JSON file."""
        logger.info(f"Loading data from {file_path}")
        with open(file_path) as f:
            return json.load(f)

    def import_tournaments(self, data: dict) -> None:
        """Import tournament records."""
        logger.info(f"Importing {len(data.get('tournaments', []))} tournaments")
        for tournament_data in data.get("tournaments", []):
            # Check if tournament already exists
            existing = (
                self.session.query(Tournament)
                .filter_by(source_id=tournament_data.get("id"))
                .first()
            )

            if existing:
                source_id = tournament_data.get("id")
                logger.info(
                    f"Tournament {tournament_data['name']} already exists (source_id: {source_id})"
                )
                self.tournament_map[tournament_data["id"]] = existing
                continue

            tournament = Tournament(
                name=tournament_data["name"],
                date=datetime.fromisoformat(tournament_data["date"]),
                format=tournament_data.get("format", "Unknown"),
                location=tournament_data.get("location"),
                num_rounds=tournament_data.get("num_rounds", 8),
                source_url=tournament_data.get("source_url"),
                source_id=tournament_data.get("id"),
            )
            self.session.add(tournament)
            self.tournament_map[tournament_data["id"]] = tournament
            logger.info(f"Added tournament: {tournament.name}")

    def import_players(self, data: dict) -> None:
        """Import player records."""
        logger.info(f"Importing {len(data.get('players', []))} players")
        for player_data in data.get("players", []):
            # Check if player already exists
            existing = self.session.query(Player).filter_by(source_id=player_data.get("id")).first()

            if existing:
                source_id = player_data.get("id")
                logger.info(f"Player {player_data['name']} already exists (source_id: {source_id})")
                self.player_map[player_data["id"]] = existing
                continue

            player = Player(
                name=player_data["name"],
                source_id=player_data.get("id"),
            )
            self.session.add(player)
            self.player_map[player_data["id"]] = player
            logger.info(f"Added player: {player.name}")

    def import_cards(self, data: dict) -> None:
        """Import card records."""
        logger.info(f"Importing {len(data.get('cards', []))} cards")
        for card_data in data.get("cards", []):
            # Check if card already exists by name (or scryfall_id if available)
            existing = None
            if card_data.get("scryfall_id"):
                existing = (
                    self.session.query(Card)
                    .filter_by(scryfall_id=card_data.get("scryfall_id"))
                    .first()
                )

            if existing:
                scryfall_id = card_data.get("scryfall_id")
                logger.info(f"Card {card_data['name']} already exists (scryfall_id: {scryfall_id})")
                self.card_map[card_data["id"]] = existing
                continue

            card = Card(
                name=card_data["name"],
                mana_cost=card_data.get("mana_cost"),
                card_type=card_data.get("card_type"),
                scryfall_id=card_data.get("scryfall_id"),
            )
            self.session.add(card)
            self.card_map[card_data["id"]] = card
            logger.info(f"Added card: {card.name}")

    def import_decks(self, data: dict) -> None:
        """Import deck records."""
        logger.info(f"Importing {len(data.get('decks', []))} decks")
        for deck_data in data.get("decks", []):
            # Check if deck already exists
            existing = self.session.query(Deck).filter_by(source_id=deck_data.get("id")).first()

            if existing:
                logger.info(
                    f"Deck {deck_data['name']} already exists (source_id: {deck_data.get('id')})"
                )
                self.deck_map[deck_data["id"]] = existing
                continue

            deck = Deck(
                name=deck_data["name"],
                format=deck_data.get("format", "Unknown"),
                archetype=deck_data.get("archetype"),
                source_id=deck_data.get("id"),
            )
            self.session.add(deck)
            self.session.flush()  # Flush to get the ID

            # Add cards to deck
            for card_entry in deck_data.get("cards", []):
                card_id = card_entry["card_id"]
                if card_id not in self.card_map:
                    logger.warning(f"Card {card_id} not found for deck {deck_data['name']}")
                    continue

                card_in_deck = CardInDeck(
                    deck_id=deck.id,
                    card_id=self.card_map[card_id].id,
                    zone=card_entry.get("zone", "main"),
                    quantity=card_entry.get("quantity", 1),
                )
                self.session.add(card_in_deck)

            self.deck_map[deck_data["id"]] = deck
            logger.info(
                f"Added deck: {deck.name} with {len(deck_data.get('cards', []))} card slots"
            )

    def import_tournament_entries(self, data: dict) -> None:
        """Import tournament entries (player registrations)."""
        logger.info(f"Importing {len(data.get('tournament_entries', []))} tournament entries")
        for entry_data in data.get("tournament_entries", []):
            tournament_id = entry_data["tournament_id"]
            player_id = entry_data["player_id"]
            deck_id = entry_data["deck_id"]

            if tournament_id not in self.tournament_map:
                logger.warning(f"Tournament {tournament_id} not found")
                continue
            if player_id not in self.player_map:
                logger.warning(f"Player {player_id} not found")
                continue
            if deck_id not in self.deck_map:
                logger.warning(f"Deck {deck_id} not found")
                continue

            # Check if entry already exists
            existing = (
                self.session.query(TournamentEntry)
                .filter_by(
                    tournament_id=self.tournament_map[tournament_id].id,
                    player_id=self.player_map[player_id].id,
                )
                .first()
            )

            if existing:
                logger.info(
                    f"Entry already exists for {self.player_map[player_id].name} in "
                    f"{self.tournament_map[tournament_id].name}"
                )
                self.entry_map[(tournament_id, player_id)] = existing
                continue

            entry = TournamentEntry(
                tournament_id=self.tournament_map[tournament_id].id,
                player_id=self.player_map[player_id].id,
                deck_id=self.deck_map[deck_id].id,
                seed=entry_data.get("seed"),
                final_placement=entry_data.get("final_placement"),
            )
            self.session.add(entry)
            self.session.flush()
            self.entry_map[(tournament_id, player_id)] = entry
            logger.info(
                f"Added entry: {self.player_map[player_id].name} "
                f"({self.deck_map[deck_id].name}) in "
                f"{self.tournament_map[tournament_id].name}"
            )

    def import_matches(self, data: dict) -> None:
        """Import match results."""
        logger.info(f"Importing {len(data.get('matches', []))} matches")
        for match_data in data.get("matches", []):
            tournament_id = match_data["tournament_id"]
            if tournament_id not in self.tournament_map:
                logger.warning(f"Tournament {tournament_id} not found for match")
                continue

            # For now, we'll skip match importing since it requires more complex
            # mapping of seeds to entries. This can be enhanced later.
            logger.debug(
                f"Match import skipped for round {match_data.get('round_num')} in {tournament_id}"
            )

    def run(self, file_path: Path) -> None:
        """Execute the full import pipeline."""
        try:
            data = self.load_json(file_path)

            # Import in order of dependencies
            self.import_tournaments(data)
            self.import_players(data)
            self.import_cards(data)
            self.import_decks(data)
            self.import_tournament_entries(data)
            self.import_matches(data)

            # Commit all changes
            self.session.commit()
            logger.info("Import completed successfully")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Import failed: {e}", exc_info=True)
            raise


def main() -> None:
    """CLI entry point for tournament importer."""
    parser = argparse.ArgumentParser(
        description="Import tournament data from JSON format into PostgreSQL"
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to a tournament JSON file or directory containing JSON files",
    )
    args = parser.parse_args()

    if not args.source.exists():
        parser.error(f"Source path does not exist: {args.source}")

    session_factory = get_session_factory()

    # Handle both single file and directory inputs
    files_to_import = []
    if args.source.is_file():
        files_to_import = [args.source]
    elif args.source.is_dir():
        files_to_import = sorted(args.source.glob("*.json"))

    if not files_to_import:
        parser.error(f"No JSON files found in {args.source}")

    for file_path in files_to_import:
        logger.info(f"\n--- Importing from {file_path.name} ---")
        with session_factory() as session:
            importer = TournamentImporter(session)
            importer.run(file_path)


if __name__ == "__main__":
    main()
