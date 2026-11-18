-- PostgreSQL matchup query for the selected schema.
-- Only completed, non-bye matches count. Equal game scores are a match draw.
-- A/B follows canonical player UUID order (playera > playerb), not archetype order.
-- Bind :format_filter (text or NULL), :tournament_id (UUID or NULL), :min_matches.
WITH matchups AS (
    SELECT
        COALESCE(da.archetype, da.title) AS archetype_a,
        COALESCE(db.archetype, db.title) AS archetype_b,
        COUNT(*) AS matches_played,
        COUNT(*) FILTER (WHERE m.wina > m.winb) AS wins_a,
        COUNT(*) FILTER (WHERE m.winb > m.wina) AS wins_b,
        COUNT(*) FILTER (WHERE m.wina = m.winb) AS draws
    FROM tournament_match m
    JOIN tournamententry ea ON ea.player = m.playera AND ea.tournament = m.tournament
    JOIN tournamententry eb ON eb.player = m.playerb AND eb.tournament = m.tournament
    JOIN deck da ON da.pk_deck = ea.deck
    JOIN deck db ON db.pk_deck = eb.deck
    JOIN tournament t ON t.pk_tournament = m.tournament
    JOIN format f ON f.pk_format = t.format
    WHERE m.done = TRUE AND m.playerb IS NOT NULL
      AND (CAST(:format_filter AS TEXT) IS NULL OR f.name_format = :format_filter)
      AND (CAST(:tournament_id AS UUID) IS NULL OR t.pk_tournament = :tournament_id)
    GROUP BY COALESCE(da.archetype, da.title), COALESCE(db.archetype, db.title)
    HAVING COUNT(*) >= :min_matches
)
SELECT *, ROUND(wins_a::numeric / NULLIF(matches_played, 0), 4) AS win_rate_a
FROM matchups
ORDER BY matches_played DESC, archetype_a, archetype_b;
