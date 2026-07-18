-- [history-001] 2026-06-13: Historical data sync — playoff brackets + per-player weekly stats.
-- New tables follow the conventions in schema.sql (INT unsigned AUTO_INCREMENT PKs,
-- sleeper_* / *_sleeper_roster_id naming mirroring the Matchups table) and carry
-- UNIQUE keys on their natural keys so backfills can upsert without ever duplicating.

-- Winners + losers playoff brackets, one row per bracket match per season.
CREATE TABLE PlayoffMatchups (
    playoff_matchup_id INT unsigned NOT NULL AUTO_INCREMENT,
    year INT NOT NULL,
    round INT NOT NULL,
    bracket ENUM('winners', 'losers') NOT NULL,
    sleeper_matchup_id INT NOT NULL,
    sleeper_roster_id INT DEFAULT NULL,
    opponent_sleeper_roster_id INT DEFAULT NULL,
    winner_sleeper_roster_id INT DEFAULT NULL,
    loser_sleeper_roster_id INT DEFAULT NULL,
    placement INT DEFAULT NULL,
    PRIMARY KEY (playoff_matchup_id),
    UNIQUE KEY uq_playoff_matchup (year, bracket, sleeper_matchup_id),
    INDEX idx_playoff_matchups_year_bracket (year, bracket)
);

-- Per-player, per-week league-scored fantasy points (starters + bench).
CREATE TABLE PlayerWeeklyStats (
    player_weekly_stat_id INT unsigned NOT NULL AUTO_INCREMENT,
    year INT NOT NULL,
    week INT NOT NULL,
    sleeper_roster_id INT NOT NULL,
    player_sleeper_id INT NOT NULL,
    points FLOAT NOT NULL DEFAULT 0,
    is_starter BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (player_weekly_stat_id),
    UNIQUE KEY uq_player_week (year, week, sleeper_roster_id, player_sleeper_id),
    INDEX idx_player_weekly_player (player_sleeper_id),
    INDEX idx_player_weekly_roster_year_week (sleeper_roster_id, year, week)
);

-- Backfill creates Matchups rows for all seasons (the live sync only UPDATEs).
-- Add a natural-key UNIQUE so those upserts cannot create duplicate matchup rows.
-- NOTE: if the live Matchups table already contains duplicates, dedup them before
-- running this statement, e.g.:
--   DELETE m1 FROM Matchups m1
--   JOIN Matchups m2
--     ON m1.year = m2.year AND m1.week = m2.week
--    AND m1.sleeper_roster_id = m2.sleeper_roster_id
--    AND m1.matchup_id > m2.matchup_id;
ALTER TABLE Matchups
    ADD UNIQUE KEY uq_matchup (year, week, sleeper_roster_id);

-- Extend the SyncStatus audit log to cover the new backfill/sync items.
ALTER TABLE SyncStatus
    MODIFY COLUMN sync_item ENUM(
        'teams', 'league_state', 'players', 'matchups', 'transactions',
        'playoffs', 'player_stats', 'draft_picks', 'backfill'
    ) NOT NULL;
