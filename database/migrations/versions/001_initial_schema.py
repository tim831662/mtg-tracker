"""Create initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-11-03 14:36:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tournaments table
    op.create_table(
        "tournaments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("format", sa.String(50), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("num_rounds", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tournaments"),
        sa.UniqueConstraint("source_id", name="uq_tournaments_source_id"),
    )
    op.create_index("ix_tournaments_date", "tournaments", ["date"])
    op.create_index("ix_tournaments_source_id", "tournaments", ["source_id"])

    # Create players table
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_players"),
        sa.UniqueConstraint("source_id", name="uq_players_source_id"),
    )
    op.create_index("ix_players_name", "players", ["name"])
    op.create_index("ix_players_source_id", "players", ["source_id"])

    # Create cards table
    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("mana_cost", sa.String(50), nullable=True),
        sa.Column("card_type", sa.String(255), nullable=True),
        sa.Column("scryfall_id", sa.String(36), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_cards"),
        sa.UniqueConstraint("scryfall_id", name="uq_cards_scryfall_id"),
    )
    op.create_index("ix_cards_name", "cards", ["name"])
    op.create_index("ix_cards_scryfall_id", "cards", ["scryfall_id"])

    # Create decks table
    op.create_table(
        "decks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("format", sa.String(50), nullable=False),
        sa.Column("archetype", sa.String(255), nullable=True),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_decks"),
        sa.UniqueConstraint("source_id", name="uq_decks_source_id"),
    )
    op.create_index("ix_decks_source_id", "decks", ["source_id"])

    # Create cards_in_decks table
    op.create_table(
        "cards_in_decks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("deck_id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("zone", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_cards_in_decks"),
        sa.ForeignKeyConstraint(["deck_id"], ["decks.id"], name="fk_cards_in_decks_deck_id_decks"),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], name="fk_cards_in_decks_card_id_cards"),
        sa.UniqueConstraint("deck_id", "card_id", "zone", name="uq_deck_card_zone"),
    )
    op.create_index("ix_cards_in_decks_deck_id", "cards_in_decks", ["deck_id"])

    # Create tournament_entries table
    op.create_table(
        "tournament_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("deck_id", sa.Integer(), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("final_placement", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_tournament_entries"),
        sa.ForeignKeyConstraint(
            ["tournament_id"], ["tournaments.id"], name="fk_tournament_entries_tournament_id_tournaments"
        ),
        sa.ForeignKeyConstraint(
            ["player_id"], ["players.id"], name="fk_tournament_entries_player_id_players"
        ),
        sa.ForeignKeyConstraint(["deck_id"], ["decks.id"], name="fk_tournament_entries_deck_id_decks"),
        sa.UniqueConstraint("tournament_id", "player_id", name="uq_tournament_player"),
    )
    op.create_index("ix_tournament_entries_tournament_id", "tournament_entries", ["tournament_id"])
    op.create_index("ix_tournament_entries_player_id", "tournament_entries", ["player_id"])

    # Create tournament_matches table
    op.create_table(
        "tournament_matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("round_num", sa.Integer(), nullable=False),
        sa.Column("player_one_id", sa.Integer(), nullable=False),
        sa.Column("player_two_id", sa.Integer(), nullable=True),
        sa.Column("winner_id", sa.Integer(), nullable=True),
        sa.Column("player_one_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("player_two_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("draws", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_tournament_matches"),
        sa.ForeignKeyConstraint(
            ["tournament_id"], ["tournaments.id"], name="fk_tournament_matches_tournament_id_tournaments"
        ),
        sa.ForeignKeyConstraint(
            ["player_one_id"],
            ["tournament_entries.id"],
            name="fk_tournament_matches_player_one_id_tournament_entries",
        ),
        sa.ForeignKeyConstraint(
            ["player_two_id"],
            ["tournament_entries.id"],
            name="fk_tournament_matches_player_two_id_tournament_entries",
        ),
        sa.ForeignKeyConstraint(
            ["winner_id"],
            ["tournament_entries.id"],
            name="fk_tournament_matches_winner_id_tournament_entries",
        ),
    )
    op.create_index("ix_tournament_matches_tournament_id", "tournament_matches", ["tournament_id"])
    op.create_index("ix_tournament_matches_player_one_id", "tournament_matches", ["player_one_id"])


def downgrade() -> None:
    op.drop_table("tournament_matches")
    op.drop_table("tournament_entries")
    op.drop_table("cards_in_decks")
    op.drop_table("decks")
    op.drop_table("cards")
    op.drop_table("players")
    op.drop_table("tournaments")
