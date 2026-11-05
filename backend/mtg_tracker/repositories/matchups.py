"""SQL for matchup win-rate analytics.

The query below uses SUM(CASE ...) instead of PostgreSQL's COUNT(*) FILTER so
the same statement runs on PostgreSQL (production) and SQLite (tests). The
idiomatic PostgreSQL version lives in database/queries/matchup_win_rates.sql.

Definitions:
  * A "match" is a tournament_matches row with both players; byes
    (player_two_id IS NULL) are excluded by the join on player two.
  * Draws (winner_id IS NULL with two players) count toward matches_played
    but toward neither side's wins.
  * Rows are directional: ("Aggro", "Control") covers matches where the
    Aggro player was seated as player one.
  * Decks without an archetype fall back to the deck name so every match
    still contributes to a matchup row.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

MATCHUP_WIN_RATE_SQL = text(
    """
    SELECT
        COALESCE(da.archetype, da.name) AS archetype_a,
        COALESCE(db.archetype, db.name) AS archetype_b,
        COUNT(*) AS matches_played,
        SUM(CASE WHEN m.winner_id = e1.id THEN 1 ELSE 0 END) AS wins_a,
        SUM(CASE WHEN m.winner_id = e2.id THEN 1 ELSE 0 END) AS wins_b,
        SUM(CASE WHEN m.winner_id IS NULL THEN 1 ELSE 0 END) AS draws
    FROM tournament_matches m
    JOIN tournament_entries e1 ON e1.id = m.player_one_id
    JOIN tournament_entries e2 ON e2.id = m.player_two_id
    JOIN decks da ON da.id = e1.deck_id
    JOIN decks db ON db.id = e2.deck_id
    JOIN tournaments t ON t.id = m.tournament_id
    WHERE m.player_two_id IS NOT NULL
      AND (:format_filter IS NULL OR t.format = :format_filter)
      AND (:tournament_id IS NULL OR m.tournament_id = :tournament_id)
    GROUP BY COALESCE(da.archetype, da.name), COALESCE(db.archetype, db.name)
    HAVING COUNT(*) >= :min_matches
    ORDER BY matches_played DESC, archetype_a, archetype_b
    """
)


class MatchupRepository:
    """Owns matchup analytics SQL; services compute derived rates."""

    @staticmethod
    def matchup_rows(
        session: Session,
        *,
        format_filter: str | None = None,
        tournament_id: int | None = None,
        min_matches: int = 1,
    ) -> list:
        result = session.execute(
            MATCHUP_WIN_RATE_SQL,
            {
                "format_filter": format_filter,
                "tournament_id": tournament_id,
                "min_matches": min_matches,
            },
        )
        return result.all()
