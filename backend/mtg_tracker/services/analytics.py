"""Matchup and metagame analytics business logic."""

import logging

from sqlalchemy.orm import Session

from mtg_tracker.repositories.matchups import MatchupRepository

logger = logging.getLogger(__name__)


class MatchupService:
    """Business logic for matchup win-rate analytics."""

    @staticmethod
    def matchup_win_rates(
        session: Session,
        *,
        format_filter: str | None = None,
        tournament_id: int | None = None,
        min_matches: int = 1,
    ) -> list[dict]:
        """Return directional archetype-pair win rates.

        Byes (matches without an opponent) are excluded by the repository
        query. Drawn matches count toward matches_played but toward neither
        side's wins, so win_rate_a = wins_a / matches_played.
        """
        rows = MatchupRepository.matchup_rows(
            session,
            format_filter=format_filter,
            tournament_id=tournament_id,
            min_matches=min_matches,
        )
        results = []
        for row in rows:
            matches_played = row.matches_played or 0
            wins_a = row.wins_a or 0
            results.append(
                {
                    "archetype_a": row.archetype_a,
                    "archetype_b": row.archetype_b,
                    "matches_played": matches_played,
                    "wins_a": wins_a,
                    "wins_b": row.wins_b or 0,
                    "draws": row.draws or 0,
                    "win_rate_a": round(wins_a / matches_played, 4) if matches_played else 0.0,
                }
            )
        return results
