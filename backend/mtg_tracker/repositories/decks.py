"""SQL queries for decks, decklists, and tournament appearances."""

from sqlalchemy.orm import Session

from mtg_tracker.models import Card, CardInDeck, Deck, Player, Tournament, TournamentEntry


class DeckRepository:
    """Owns deck SQL; keep HTTP and business concerns outside this layer."""

    @staticmethod
    def list_all(
        session: Session,
        format_filter: str | None = None,
        archetype: str | None = None,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Deck]:
        query = session.query(Deck).order_by(Deck.name, Deck.id)
        if format_filter:
            query = query.filter(Deck.format == format_filter)
        if archetype:
            query = query.filter(Deck.archetype == archetype)
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def count(
        session: Session,
        format_filter: str | None = None,
        archetype: str | None = None,
    ) -> int:
        query = session.query(Deck)
        if format_filter:
            query = query.filter(Deck.format == format_filter)
        if archetype:
            query = query.filter(Deck.archetype == archetype)
        return query.count()

    @staticmethod
    def get_by_id(session: Session, deck_id: int) -> Deck | None:
        return session.query(Deck).filter_by(id=deck_id).first()

    @staticmethod
    def get_by_source_id(session: Session, source_id: str) -> Deck | None:
        return session.query(Deck).filter_by(source_id=source_id).first()

    @staticmethod
    def cards(session: Session, deck_id: int) -> list[dict]:
        """Return the deck's card slots ordered by zone then card name."""
        rows = (
            session.query(CardInDeck, Card)
            .join(Card, Card.id == CardInDeck.card_id)
            .filter(CardInDeck.deck_id == deck_id)
            .order_by(CardInDeck.zone, Card.name)
            .all()
        )
        return [
            {
                "name": card.name,
                "quantity": entry.quantity,
                "zone": entry.zone,
                "mana_cost": card.mana_cost,
            }
            for entry, card in rows
        ]

    @staticmethod
    def appearances(session: Session, deck_id: int) -> list[dict]:
        """Return the tournaments a deck appeared in, most recent first."""
        rows = (
            session.query(Tournament, Player, TournamentEntry.final_placement)
            .join(TournamentEntry, TournamentEntry.tournament_id == Tournament.id)
            .join(Player, Player.id == TournamentEntry.player_id)
            .filter(TournamentEntry.deck_id == deck_id)
            .order_by(Tournament.date.desc(), Tournament.id)
            .all()
        )
        return [
            {
                "tournament_id": tournament.id,
                "tournament_name": tournament.name,
                "tournament_date": tournament.date,
                "player_id": player.id,
                "player_name": player.name,
                "final_placement": final_placement,
            }
            for tournament, player, final_placement in rows
        ]
