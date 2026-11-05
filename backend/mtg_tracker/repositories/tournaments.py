"""SQL queries for tournaments and their standings."""

from sqlalchemy.orm import Session, selectinload

from mtg_tracker.models import Deck, Player, Tournament, TournamentEntry


class TournamentRepository:
    """Owns tournament SQL; keep HTTP and business concerns outside this layer."""

    @staticmethod
    def list_all(
        session: Session,
        format_filter: str | None = None,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Tournament]:
        query = (
            session.query(Tournament)
            .options(selectinload(Tournament.entries))
            .order_by(Tournament.date.desc(), Tournament.id)
        )
        if format_filter:
            query = query.filter(Tournament.format == format_filter)
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def count(session: Session, format_filter: str | None = None) -> int:
        query = session.query(Tournament)
        if format_filter:
            query = query.filter(Tournament.format == format_filter)
        return query.count()

    @staticmethod
    def get_by_id(session: Session, tournament_id: int) -> Tournament | None:
        return (
            session.query(Tournament)
            .options(selectinload(Tournament.entries))
            .filter_by(id=tournament_id)
            .first()
        )

    @staticmethod
    def get_by_source_id(session: Session, source_id: str) -> Tournament | None:
        return session.query(Tournament).filter_by(source_id=source_id).first()

    @staticmethod
    def standings(session: Session, tournament_id: int) -> list[dict]:
        """Return one row per entry, ordered by final placement (nulls last)."""
        rows = (
            session.query(TournamentEntry, Player, Deck)
            .join(Player, Player.id == TournamentEntry.player_id)
            .join(Deck, Deck.id == TournamentEntry.deck_id)
            .filter(TournamentEntry.tournament_id == tournament_id)
            .all()
        )
        standings = [
            {
                "entry_id": entry.id,
                "player_id": player.id,
                "player_name": player.name,
                "deck_id": deck.id,
                "deck_name": deck.name,
                "archetype": deck.archetype,
                "seed": entry.seed,
                "final_placement": entry.final_placement,
            }
            for entry, player, deck in rows
        ]
        standings.sort(key=lambda s: (s["final_placement"] is None, s["final_placement"] or 0))
        return standings
