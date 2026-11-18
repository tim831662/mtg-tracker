"""UUID competition tables adapted from the selected schema branch."""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mtg_tracker.db.base import Base
from mtg_tracker.models.catalog import Card, Format


class Player(Base):
    __tablename__ = "player"

    id: Mapped[UUID] = mapped_column(
        "pk_player", Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column("name_real", String(64))
    username: Mapped[str | None] = mapped_column(String(32), unique=True)
    source_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    __table_args__ = (
        Index("idx_player__upper__username", func.upper(username)),
        Index("idx_player__upper__name_real", func.upper(name), unique=True),
    )


class Deck(Base):
    __tablename__ = "deck"

    id: Mapped[UUID] = mapped_column(
        "pk_deck", Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column("title", String(64))
    format_id: Mapped[UUID] = mapped_column("format", ForeignKey("format.pk_format"))
    archetype: Mapped[str | None] = mapped_column(String(255))
    source_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    format_rule: Mapped[Format] = relationship(lazy="joined")
    cards: Mapped[list["CardInDeck"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )
    __table_args__ = (Index("idx_deck__upper__name_deck", func.upper(name)),)

    @property
    def format(self) -> str:
        return self.format_rule.name


class CardInDeck(Base):
    __tablename__ = "card_in_deck"

    deck_id: Mapped[UUID] = mapped_column("deck", ForeignKey("deck.pk_deck"), primary_key=True)
    card_id: Mapped[UUID] = mapped_column("card", ForeignKey("card.pk_card"), primary_key=True)
    # A card may appear in both zones; extend the branch's two-column key.
    zone: Mapped[str] = mapped_column(String(20), primary_key=True, server_default="main")
    quantity: Mapped[int] = mapped_column("amount", SmallInteger)
    deck: Mapped[Deck] = relationship(back_populates="cards")
    card: Mapped[Card] = relationship()
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("zone IN ('main', 'sideboard')", name="zone_valid"),
    )


class Tournament(Base):
    __tablename__ = "tournament"

    id: Mapped[UUID] = mapped_column(
        "pk_tournament",
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[str | None] = mapped_column("id", String(126), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column("loc", String(255))
    format_id: Mapped[UUID] = mapped_column("format", ForeignKey("format.pk_format"))
    date: Mapped[date] = mapped_column("occurred", Date)
    description: Mapped[str | None] = mapped_column(Text)
    num_rounds: Mapped[int] = mapped_column(Integer, server_default="8")
    source_url: Mapped[str | None] = mapped_column(Text)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    format_rule: Mapped[Format] = relationship(lazy="joined")
    entries: Mapped[list["TournamentEntry"]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )
    matches: Mapped[list["TournamentMatch"]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )
    __table_args__ = (
        Index("idx_tournament__id__upper", func.upper(source_id), unique=True),
        Index("idx_tournament__upper_loc", func.upper(location)),
        Index("idx_tournament__occurred", date.desc()),
        CheckConstraint("num_rounds > 0", name="rounds_positive"),
    )

    @property
    def format(self) -> str:
        return self.format_rule.name


class TournamentEntry(Base):
    __tablename__ = "tournamententry"

    player_id: Mapped[UUID] = mapped_column(
        "player", ForeignKey("player.pk_player"), primary_key=True
    )
    tournament_id: Mapped[UUID] = mapped_column(
        "tournament", ForeignKey("tournament.pk_tournament"), primary_key=True
    )
    deck_id: Mapped[UUID] = mapped_column("deck", ForeignKey("deck.pk_deck"))
    final_placement: Mapped[int | None] = mapped_column("placement", SmallInteger)
    seed: Mapped[int | None] = mapped_column(Integer)
    player: Mapped[Player] = relationship()
    tournament: Mapped[Tournament] = relationship(back_populates="entries")
    deck: Mapped[Deck] = relationship()


class TournamentMatch(Base):
    __tablename__ = "tournament_match"

    id: Mapped[UUID] = mapped_column(
        "pk_match", Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    tournament_id: Mapped[UUID] = mapped_column(
        "tournament", ForeignKey("tournament.pk_tournament")
    )
    round_num: Mapped[int] = mapped_column("round", SmallInteger)
    player_one_id: Mapped[UUID] = mapped_column("playera", ForeignKey("player.pk_player"))
    player_two_id: Mapped[UUID | None] = mapped_column("playerb", ForeignKey("player.pk_player"))
    player_one_wins: Mapped[int] = mapped_column("wina", SmallInteger, server_default="0")
    player_two_wins: Mapped[int] = mapped_column("winb", SmallInteger, server_default="0")
    draws: Mapped[int] = mapped_column(SmallInteger, server_default="0")
    done: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    tournament: Mapped[Tournament] = relationship(back_populates="matches")
    __table_args__ = (
        CheckConstraint("wina >= 0 AND winb >= 0 AND draws >= 0", name="results_nonnegative"),
        CheckConstraint("playerb IS NULL OR playera > playerb", name="player_order"),
        CheckConstraint("playerb IS NOT NULL OR (winb = 0 AND draws = 0)", name="bye_valid"),
        CheckConstraint("round > 0", name="round_positive"),
        ForeignKeyConstraint(
            ["playera", "tournament"],
            ["tournamententry.player", "tournamententry.tournament"],
            name="fk_match_playera_entry",
        ),
        ForeignKeyConstraint(
            ["playerb", "tournament"],
            ["tournamententry.player", "tournamententry.tournament"],
            name="fk_match_playerb_entry",
        ),
    )
