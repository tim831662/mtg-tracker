"""Tournament, player, deck, and match models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mtg_tracker.db.base import Base


class Tournament(Base):
    """A Magic: The Gathering tournament event."""

    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Standard", "Pioneer"
    location: Mapped[str | None] = mapped_column(String(255))
    num_rounds: Mapped[int] = mapped_column(Integer, default=8)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    entries: Mapped[list["TournamentEntry"]] = relationship(
        "TournamentEntry", back_populates="tournament", cascade="all, delete-orphan"
    )
    matches: Mapped[list["TournamentMatch"]] = relationship(
        "TournamentMatch", back_populates="tournament", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tournament {self.id}: {self.name} ({self.format})>"


class Player(Base):
    """A Magic player."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    entries: Mapped[list["TournamentEntry"]] = relationship(
        "TournamentEntry", back_populates="player", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Player {self.id}: {self.name}>"


class Deck(Base):
    """A Magic deck."""

    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    archetype: Mapped[str | None] = mapped_column(String(255))
    source_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    entries: Mapped[list["TournamentEntry"]] = relationship(
        "TournamentEntry", back_populates="deck", cascade="all, delete-orphan"
    )
    cards: Mapped[list["CardInDeck"]] = relationship(
        "CardInDeck", back_populates="deck", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Deck {self.id}: {self.name}>"


class Card(Base):
    """A Magic card."""

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mana_cost: Mapped[str | None] = mapped_column(String(50))
    card_type: Mapped[str | None] = mapped_column(String(255))
    scryfall_id: Mapped[str | None] = mapped_column(String(36), unique=True, index=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    deck_cards: Mapped[list["CardInDeck"]] = relationship(
        "CardInDeck", back_populates="card", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Card {self.id}: {self.name}>"


class CardInDeck(Base):
    """Association table for cards in decks with quantity and zone."""

    __tablename__ = "cards_in_decks"
    __table_args__ = (UniqueConstraint("deck_id", "card_id", "zone", name="uq_deck_card_zone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"), nullable=False, index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), nullable=False, index=True)
    zone: Mapped[str] = mapped_column(String(20), nullable=False)  # "main" or "sideboard"
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    deck: Mapped[Deck] = relationship("Deck", back_populates="cards")
    card: Mapped[Card] = relationship("Card", back_populates="deck_cards")

    def __repr__(self) -> str:
        return f"<CardInDeck deck={self.deck_id} card={self.card_id} qty={self.quantity}>"


class TournamentEntry(Base):
    """A player's entry in a tournament with their deck."""

    __tablename__ = "tournament_entries"
    __table_args__ = (UniqueConstraint("tournament_id", "player_id", name="uq_tournament_player"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id"), nullable=False, index=True
    )
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"), nullable=False, index=True)
    seed: Mapped[int | None] = mapped_column(Integer)
    final_placement: Mapped[int | None] = mapped_column(Integer)

    tournament: Mapped[Tournament] = relationship("Tournament", back_populates="entries")
    player: Mapped[Player] = relationship("Player", back_populates="entries")
    deck: Mapped[Deck] = relationship("Deck", back_populates="entries")
    matches_as_player_one: Mapped[list["TournamentMatch"]] = relationship(
        "TournamentMatch",
        foreign_keys="TournamentMatch.player_one_id",
        back_populates="player_one",
        cascade="all, delete-orphan",
    )
    matches_as_player_two: Mapped[list["TournamentMatch"]] = relationship(
        "TournamentMatch",
        foreign_keys="TournamentMatch.player_two_id",
        back_populates="player_two",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TournamentEntry tournament={self.tournament_id} player={self.player_id}>"


class TournamentMatch(Base):
    """A match result between two players in a tournament."""

    __tablename__ = "tournament_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id"), nullable=False, index=True
    )
    round_num: Mapped[int] = mapped_column(Integer, nullable=False)
    player_one_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_entries.id"), nullable=False, index=True
    )
    player_two_id: Mapped[int | None] = mapped_column(
        ForeignKey("tournament_entries.id"), index=True
    )
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("tournament_entries.id"))
    # For draws or byes: None winner means draw or bye
    player_one_wins: Mapped[int] = mapped_column(Integer, default=0)
    player_two_wins: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)

    tournament: Mapped[Tournament] = relationship("Tournament", back_populates="matches")
    player_one: Mapped[TournamentEntry] = relationship(
        "TournamentEntry", foreign_keys=[player_one_id], back_populates="matches_as_player_one"
    )
    player_two: Mapped[TournamentEntry | None] = relationship(
        "TournamentEntry", foreign_keys=[player_two_id], back_populates="matches_as_player_two"
    )

    def __repr__(self) -> str:
        return (
            f"<TournamentMatch round={self.round_num} {self.player_one_id} vs {self.player_two_id}>"
        )
