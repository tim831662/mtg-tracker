"""Card catalog and format tables from the selected schema-branch design.

Physical identifiers follow PostgreSQL's folding of the original unquoted SQL.
Python attributes retain readable names for the existing services and API.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from mtg_tracker.db.base import Base


class Mana(Base):
    __tablename__ = "mana"

    id: Mapped[int] = mapped_column("mana", SmallInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(9), unique=True)
    abbreviation: Mapped[str] = mapped_column("abbr", String(1), unique=True)


class Rarity(Base):
    __tablename__ = "rarity"

    id: Mapped[int] = mapped_column(
        "pk_rarity", SmallInteger, primary_key=True, autoincrement=False
    )
    name: Mapped[str] = mapped_column("rarity", String(20), unique=True)


class Artist(Base):
    __tablename__ = "artist"

    id: Mapped[UUID] = mapped_column(
        "pk_artist", Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column("artist", String(16))
    __table_args__ = (Index("idx_artist__name", func.upper(name)),)


class Card(Base):
    __tablename__ = "card"

    id: Mapped[UUID] = mapped_column(
        "pk_card", Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column("title", String(255), unique=True)
    color_identity: Mapped[int] = mapped_column("coloridentity", SmallInteger, server_default="63")
    power: Mapped[str | None] = mapped_column(String(16))
    toughness: Mapped[str | None] = mapped_column(String(16))
    rarity_id: Mapped[int | None] = mapped_column("rarity", ForeignKey("rarity.pk_rarity"))
    mana_production_type: Mapped[int] = mapped_column(SmallInteger, server_default="0")
    mana_production_amount: Mapped[int] = mapped_column(SmallInteger, server_default="0")
    is_promo: Mapped[bool] = mapped_column("ispromo", Boolean, server_default=text("false"))
    set_code: Mapped[str | None] = mapped_column("setcode", String(8))
    description: Mapped[str | None] = mapped_column(Text)
    # Retain original text until the normalized catalog importer is finished.
    mana_cost: Mapped[str | None] = mapped_column(String(100))
    card_type: Mapped[str | None] = mapped_column("type_line", String(255))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    __table_args__ = (
        CheckConstraint("coloridentity BETWEEN 0 AND 63", name="color_identity_valid"),
        CheckConstraint("mana_production_type BETWEEN 0 AND 63", name="mana_type_valid"),
        CheckConstraint("mana_production_amount >= 0", name="mana_amount_nonnegative"),
        Index("idx_card__upper__title", func.upper(name), unique=True),
        Index("idx_card__color_identity", color_identity),
        Index("idx_card__power", power.desc()),
        Index("idx_card__tough", toughness.desc()),
        Index("idx_card__rarity", rarity_id.desc()),
        Index("idx_card__mana_production_type", mana_production_type),
        Index("idx_card__is_promo", is_promo),
        Index("idx_card__setcode", func.upper(set_code)),
    )


class ArtistWorkedOnCard(Base):
    __tablename__ = "artist__worked_on__card"

    card_id: Mapped[UUID] = mapped_column("card", ForeignKey("card.pk_card"), primary_key=True)
    artist_id: Mapped[UUID] = mapped_column(
        "artist", ForeignKey("artist.pk_artist"), primary_key=True
    )


class Keyword(Base):
    __tablename__ = "keyword"

    card_id: Mapped[UUID] = mapped_column("card", ForeignKey("card.pk_card"), primary_key=True)
    word: Mapped[str] = mapped_column(String(20), primary_key=True)
    __table_args__ = (
        CheckConstraint("word = UPPER(word)", name="word_uppercase"),
        Index("indx_keyword__word", word),
    )


class Subtype(Base):
    __tablename__ = "subtype"

    card_id: Mapped[UUID] = mapped_column("card", ForeignKey("card.pk_card"), primary_key=True)
    name: Mapped[str] = mapped_column("subtype", String(20), primary_key=True)
    __table_args__ = (CheckConstraint("subtype = UPPER(subtype)", name="subtype_uppercase"),)


class CardManaCost(Base):
    __tablename__ = "card_mana_cost"

    card_id: Mapped[UUID] = mapped_column("card", ForeignKey("card.pk_card"), primary_key=True)
    mana_type: Mapped[int] = mapped_column("type", SmallInteger, primary_key=True)
    amount: Mapped[int] = mapped_column(SmallInteger, server_default="1")
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("type > 0 AND type <= 63", name="type_valid"),
    )


class CardIsType(Base):
    __tablename__ = "card_is_type"

    card_id: Mapped[UUID] = mapped_column("card", ForeignKey("card.pk_card"), primary_key=True)
    name: Mapped[str] = mapped_column("type", String(20), primary_key=True)


class Format(Base):
    __tablename__ = "format"

    id: Mapped[UUID] = mapped_column(
        "pk_format", Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column("name_format", String(16), unique=True)
    minimum_size: Mapped[int] = mapped_column("minsz", SmallInteger, server_default="60")
    copy_limit: Mapped[int] = mapped_column("copylimit", SmallInteger, server_default="4")
    __table_args__ = (
        CheckConstraint("minsz > 0", name="minimum_size_positive"),
        CheckConstraint("copylimit >= 0", name="copy_limit_nonnegative"),
        Index("idx_format__upper__name", func.upper(name), unique=True),
    )


class FormatRestriction(Base):
    __tablename__ = "formatrestriction"

    format_id: Mapped[UUID] = mapped_column(
        "format", ForeignKey("format.pk_format"), primary_key=True
    )
    card_id: Mapped[UUID] = mapped_column("card", ForeignKey("card.pk_card"), primary_key=True)
    maximum: Mapped[int] = mapped_column("max", SmallInteger, server_default="0")
    __table_args__ = (CheckConstraint("max >= 0", name="maximum_nonnegative"),)
