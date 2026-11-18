"""Matchup queries over the selected schema's player and composite-entry keys."""

from uuid import UUID

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session, aliased

from mtg_tracker.models import Deck, Format, Tournament, TournamentEntry, TournamentMatch


class MatchupRepository:
    @staticmethod
    def matchup_rows(
        session: Session,
        *,
        format_filter: str | None = None,
        tournament_id: UUID | None = None,
        min_matches: int = 1,
    ) -> list:
        entry_a, entry_b = aliased(TournamentEntry), aliased(TournamentEntry)
        deck_a, deck_b = aliased(Deck), aliased(Deck)
        a = func.coalesce(deck_a.archetype, deck_a.name)
        b = func.coalesce(deck_b.archetype, deck_b.name)
        match = TournamentMatch
        count = func.count(match.id)
        query = (
            session.query(
                a.label("archetype_a"),
                b.label("archetype_b"),
                count.label("matches_played"),
                func.sum(case((match.player_one_wins > match.player_two_wins, 1), else_=0)).label(
                    "wins_a"
                ),
                func.sum(case((match.player_two_wins > match.player_one_wins, 1), else_=0)).label(
                    "wins_b"
                ),
                func.sum(case((match.player_one_wins == match.player_two_wins, 1), else_=0)).label(
                    "draws"
                ),
            )
            .select_from(match)
            .join(
                entry_a,
                and_(
                    entry_a.player_id == match.player_one_id,
                    entry_a.tournament_id == match.tournament_id,
                ),
            )
            .join(
                entry_b,
                and_(
                    entry_b.player_id == match.player_two_id,
                    entry_b.tournament_id == match.tournament_id,
                ),
            )
            .join(deck_a, deck_a.id == entry_a.deck_id)
            .join(deck_b, deck_b.id == entry_b.deck_id)
            .join(Tournament, Tournament.id == match.tournament_id)
            .filter(match.done.is_(True), match.player_two_id.is_not(None))
        )
        if format_filter:
            query = query.filter(Tournament.format_rule.has(Format.name == format_filter))
        if tournament_id:
            query = query.filter(match.tournament_id == tournament_id)
        return query.group_by(a, b).having(count >= min_matches).order_by(count.desc(), a, b).all()
