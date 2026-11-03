"""
Example usage of the tournament import system.

This file demonstrates how to use the models, importer, and services
for working with MTG tournament data.
"""

# ============================================================================
# EXAMPLE 1: Import tournament data from JSON
# ============================================================================


def example_import_tournaments():
    """Import tournament data from a JSON file."""
    from pathlib import Path

    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.importers.tournaments import TournamentImporter

    # Get database session
    session_factory = get_session_factory()

    # Import data
    json_file = Path("database/seeds/sample_tournament_data.json")
    with session_factory() as session:
        importer = TournamentImporter(session)
        importer.run(json_file)

    print("✅ Import complete!")


# ============================================================================
# EXAMPLE 2: Query tournaments after import
# ============================================================================


def example_query_tournaments():
    """Query imported tournament data."""
    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.services import TournamentService

    session_factory = get_session_factory()

    with session_factory() as session:
        # Get all tournaments
        tournaments = TournamentService.list_tournaments(session)
        print(f"Found {len(tournaments)} tournaments:")
        for t in tournaments:
            print(f"  - {t.name} ({t.format}) on {t.date.date()}")

        # Get tournaments by format
        pioneer_tournaments = TournamentService.list_tournaments(session, format_filter="Pioneer")
        print(f"\nPioneer tournaments: {len(pioneer_tournaments)}")


# ============================================================================
# EXAMPLE 3: Get deck information
# ============================================================================


def example_get_deck_info():
    """Query deck information."""
    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.models import Deck
    from mtg_tracker.services import DeckService

    session_factory = get_session_factory()

    with session_factory() as session:
        # Get a deck
        deck = session.query(Deck).first()
        if not deck:
            print("No decks found")
            return

        print(f"\nDeck: {deck.name}")
        print(f"  Format: {deck.format}")
        print(f"  Archetype: {deck.archetype}")

        # Get deck composition
        main_size = DeckService.calculate_deck_size(session, deck.id)
        sideboard_size = DeckService.calculate_sideboard_size(session, deck.id)
        print(f"  Main Deck: {main_size} cards")
        print(f"  Sideboard: {sideboard_size} cards")

        # Check legality
        is_legal, errors = DeckService.validate_deck_legality(session, deck.id, deck.format)
        if is_legal:
            print(f"  ✓ Legal for {deck.format}")
        else:
            print("  ✗ Issues found:")
            for error in errors:
                print(f"    - {error}")

        # Show cards
        print("\n  Cards in deck:")
        for card_entry in deck.cards:
            print(f"    {card_entry.quantity}x {card_entry.card.name} ({card_entry.zone})")


# ============================================================================
# EXAMPLE 4: Query tournament standings
# ============================================================================


def example_tournament_standings():
    """Get tournament standings."""
    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.models import Tournament

    session_factory = get_session_factory()

    with session_factory() as session:
        # Get first tournament
        tournament = session.query(Tournament).first()
        if not tournament:
            print("No tournaments found")
            return

        print(f"\nTournament: {tournament.name}")
        print("Standings:")

        # Sort entries by placement
        entries = sorted(tournament.entries, key=lambda e: e.final_placement or 999)
        for entry in entries[:8]:  # Top 8
            print(
                f"  {entry.final_placement}. {entry.player.name} "
                f"({entry.deck.name}, {entry.deck.archetype})"
            )


# ============================================================================
# EXAMPLE 5: Create new data programmatically
# ============================================================================


def example_create_tournament():
    """Create a new tournament programmatically."""
    from datetime import datetime

    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.models import Tournament

    session_factory = get_session_factory()

    with session_factory() as session:
        # Create new tournament
        tournament = Tournament(
            name="Regional Qualifier 2024",
            date=datetime(2024, 5, 15),
            format="Standard",
            location="Regional Center",
            num_rounds=9,
            source_id="rq_2024_05",
        )
        session.add(tournament)
        session.commit()

        print(f"✅ Created tournament: {tournament.name} (ID: {tournament.id})")


# ============================================================================
# EXAMPLE 6: Analyze deck archetypes
# ============================================================================


def example_archetype_analysis():
    """Analyze archetype distribution in tournaments."""
    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.models import Deck, TournamentEntry
    from sqlalchemy import func

    session_factory = get_session_factory()

    with session_factory() as session:
        # Count decks by archetype
        archetype_counts = (
            session.query(Deck.archetype, func.count(TournamentEntry.id))
            .join(TournamentEntry, TournamentEntry.deck_id == Deck.id)
            .group_by(Deck.archetype)
            .all()
        )

        print("\nArchetype Distribution:")
        for archetype, count in archetype_counts:
            print(f"  {archetype or 'Unknown'}: {count}")


# ============================================================================
# EXAMPLE 7: Export deck data
# ============================================================================


def example_export_deck():
    """Export a deck to JSON format."""
    import json

    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.models import Deck

    session_factory = get_session_factory()

    with session_factory() as session:
        deck = session.query(Deck).first()
        if not deck:
            print("No decks found")
            return

        # Build export data
        deck_data = {
            "name": deck.name,
            "format": deck.format,
            "archetype": deck.archetype,
            "main_deck": [],
            "sideboard": [],
        }

        for card_entry in deck.cards:
            card_info = {
                "name": card_entry.card.name,
                "quantity": card_entry.quantity,
                "mana_cost": card_entry.card.mana_cost,
            }

            if card_entry.zone == "main":
                deck_data["main_deck"].append(card_info)
            else:
                deck_data["sideboard"].append(card_info)

        print("\nExported deck:")
        print(json.dumps(deck_data, indent=2))


# ============================================================================
# EXAMPLE 8: Find duplicate cards across decks
# ============================================================================


def example_find_card_usage():
    """Find which decks use specific cards."""
    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.models import Card

    session_factory = get_session_factory()

    with session_factory() as session:
        # Get most common cards
        cards = session.query(Card).all()

        print("\nCard Usage:")
        for card in cards[:5]:
            deck_count = len(card.deck_cards)
            if deck_count > 0:
                total_copies = sum(ce.quantity for ce in card.deck_cards)
                print(f"  {card.name}: in {deck_count} decks, {total_copies} total copies")


# ============================================================================
# EXAMPLE 9: Calculate format-specific statistics
# ============================================================================


def example_format_statistics():
    """Calculate statistics for a format."""
    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.models import Tournament, TournamentEntry
    from sqlalchemy import func

    session_factory = get_session_factory()

    with session_factory() as session:
        formats = (
            session.query(Tournament.format, func.count(Tournament.id))
            .group_by(Tournament.format)
            .all()
        )

        print("\nTournaments by Format:")
        for format_name, count in formats:
            print(f"  {format_name}: {count}")

            # Get average tournament size for this format
            entries = (
                session.query(func.count(TournamentEntry.id).label("total"))
                .join(Tournament)
                .filter(Tournament.format == format_name)
                .scalar()
            )
            if count > 0:
                avg_size = entries / count if count else 0
                print(f"    Average size: {avg_size:.0f} players")


# ============================================================================
# EXAMPLE 10: Migrate data to another database
# ============================================================================


def example_backup_data():
    """Export all tournament data to JSON backup."""
    import json
    from datetime import datetime

    from mtg_tracker.db.session import get_session_factory
    from mtg_tracker.models import Card, Deck, Player, Tournament

    session_factory = get_session_factory()

    with session_factory() as session:
        backup = {
            "exported_at": datetime.now().isoformat(),
            "tournaments": [
                {
                    "id": t.id,
                    "name": t.name,
                    "date": t.date.isoformat(),
                    "format": t.format,
                    "location": t.location,
                }
                for t in session.query(Tournament).all()
            ],
            "players": [{"id": p.id, "name": p.name} for p in session.query(Player).all()],
            "cards": [
                {
                    "id": c.id,
                    "name": c.name,
                    "mana_cost": c.mana_cost,
                    "card_type": c.card_type,
                }
                for c in session.query(Card).all()
            ],
            "decks": [
                {
                    "id": d.id,
                    "name": d.name,
                    "format": d.format,
                    "archetype": d.archetype,
                }
                for d in session.query(Deck).all()
            ],
        }

        with open("backup_tournament_data.json", "w") as f:
            json.dump(backup, f, indent=2)

        print("✅ Data exported to backup_tournament_data.json")


# ============================================================================
# Run examples
# ============================================================================

if __name__ == "__main__":
    import sys

    examples = {
        "1": ("Import tournaments", example_import_tournaments),
        "2": ("Query tournaments", example_query_tournaments),
        "3": ("Get deck info", example_get_deck_info),
        "4": ("Tournament standings", example_tournament_standings),
        "5": ("Create tournament", example_create_tournament),
        "6": ("Archetype analysis", example_archetype_analysis),
        "7": ("Export deck", example_export_deck),
        "8": ("Card usage", example_find_card_usage),
        "9": ("Format statistics", example_format_statistics),
        "10": ("Backup data", example_backup_data),
    }

    print("Task 3 Examples - MTG Tracker Data Import\n")
    print("Available examples:")
    for key, (desc, _) in examples.items():
        print(f"  {key}. {desc}")

    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice in examples:
            name, func = examples[choice]
            print(f"\nRunning example: {name}\n")
            try:
                func()
            except Exception as e:
                print(f"❌ Error: {e}")
                print("\nNote: Make sure PostgreSQL is running and the database is set up.")
                print("Run: uv run alembic upgrade head")
        else:
            print(f"\n❌ Unknown example: {choice}")
    else:
        print("\nUsage: python -m examples 1")
        print("(Replace 1 with the example number)")
