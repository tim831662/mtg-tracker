-- Matchup win rates by deck archetype pair (PostgreSQL).
--
-- The application runs the portable SUM(CASE ...) version in
-- backend/mtg_tracker/repositories/matchups.py; this file is the reviewed
-- PostgreSQL equivalent kept here for documentation and ad-hoc analysis.
--
-- Definitions:
--   * A "match" is a tournament_matches row with both player_one and
--     player_two; byes (player_two_id IS NULL) are excluded.
--   * Draws (winner_id IS NULL with two players) count toward
--     matches_played but toward neither side's wins.
--   * win_rate_a = wins_a / matches_played (draws count as non-wins).
--   * Rows are directional: ("Aggro", "Control") covers matches where the
--     Aggro player was seated as player one.
--   * Decks without an archetype fall back to the deck name.
--
-- Bind parameters (all optional except min_matches):
--   :format_filter   e.g. 'Standard'; NULL disables the filter
--   :tournament_id   restrict to one tournament; NULL disables the filter
--   :min_matches     exclude archetype pairs with fewer matches (default 1)

WITH matchups AS (
    SELECT
        COALESCE(da.archetype, da.name) AS archetype_a,
        COALESCE(db.archetype, db.name) AS archetype_b,
        COUNT(*) AS matches_played,
        COUNT(*) FILTER (WHERE m.winner_id = e1.id) AS wins_a,
        COUNT(*) FILTER (WHERE m.winner_id = e2.id) AS wins_b,
        COUNT(*) FILTER (WHERE m.winner_id IS NULL) AS draws
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
)
SELECT
    archetype_a,
    archetype_b,
    matches_played,
    wins_a,
    wins_b,
    draws,
    ROUND(wins_a::numeric / NULLIF(matches_played, 0), 4) AS win_rate_a
FROM matchups
ORDER BY matches_played DESC, archetype_a, archetype_b;
