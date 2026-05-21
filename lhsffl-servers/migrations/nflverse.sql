-- =============================================================================
-- nflverse Migrations
-- =============================================================================
-- Schema additions to support nflverse data integration.
-- Data is sourced from https://github.com/nflverse/nflverse-data (CC BY 4.0).
-- All rows are filtered to players whose gsis_id exists in the Players table.
--
-- Tables added:
--   NFLDraftData    - NFL draft history per player (synced annually)
--   PlayerGameLogs  - Weekly player stats and opportunity metrics (synced nightly)
-- =============================================================================


-- -----------------------------------------------------------------------------
-- [nflverse-001] Add NFLDraftData table
-- Date: 2026-03-08
--
-- Stores NFL draft context for players already tracked in the Players table.
-- Joined on gsis_id. One row per player — static data updated annually.
-- Excludes columns duplicated on Players (position, college) and low-value
-- career stat totals. Source: nflverse load_draft_picks().
-- -----------------------------------------------------------------------------
-- -----------------------------------------------------------------------------
-- [nflverse-pre] Add pfr_id to Players table
-- Date: 2026-03-08
--
-- pfr_id (Pro Football Reference ID) is needed to join against pfr_advstats
-- from nflverse. Backfilled via nflverse players + ff_playerids datasets
-- using sleeper_id as the cross-reference key.
-- -----------------------------------------------------------------------------
ALTER TABLE Players ADD COLUMN IF NOT EXISTS pfr_id VARCHAR(16) DEFAULT NULL;


-- -----------------------------------------------------------------------------
-- [nflverse-000] Extend SyncStatus.sync_item enum for nflverse sync types
-- Date: 2026-03-08
-- -----------------------------------------------------------------------------
ALTER TABLE SyncStatus
    MODIFY COLUMN sync_item ENUM(
        'teams', 'league_state', 'players', 'matchups', 'transactions',
        'nfl_draft', 'game_logs'
    ) NOT NULL;


-- -----------------------------------------------------------------------------
-- [nflverse-001] Add NFLDraftData table
CREATE TABLE IF NOT EXISTS NFLDraftData (
    nfl_draft_data_id INT unsigned NOT NULL AUTO_INCREMENT,
    gsis_id           VARCHAR(32) NOT NULL,
    nfl_draft_season  INT NOT NULL,
    round             INT NOT NULL,
    pick              INT NOT NULL,
    drafting_team     VARCHAR(8) NOT NULL,
    age_at_draft      INT DEFAULT NULL,
    allpro            INT NOT NULL DEFAULT 0,
    probowls          INT NOT NULL DEFAULT 0,
    seasons_started   INT NOT NULL DEFAULT 0,
    career_av         INT DEFAULT NULL,
    weighted_av       INT DEFAULT NULL,
    hof               BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (nfl_draft_data_id),
    UNIQUE KEY uq_nfl_draft_data_gsis (gsis_id),
    INDEX ix_nfl_draft_data_season (nfl_draft_season)
);


-- -----------------------------------------------------------------------------
-- [nflverse-002] Add PlayerGameLogs table
-- Date: 2026-03-08
--
-- Stores per-player per-week stats and opportunity metrics for the current
-- and recent seasons. Joined on gsis_id. One row per player per season per week.
-- Source: nflverse load_ff_opportunity().
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS PlayerGameLogs (
    player_game_log_id      INT unsigned NOT NULL AUTO_INCREMENT,
    gsis_id                 VARCHAR(32) NOT NULL,
    season                  INT NOT NULL,
    week                    INT NOT NULL,
    team                    VARCHAR(8) DEFAULT NULL,
    targets                 INT DEFAULT NULL,
    receptions              INT DEFAULT NULL,
    rec_air_yards           FLOAT DEFAULT NULL,
    rec_yards               FLOAT DEFAULT NULL,
    rec_touchdowns          INT DEFAULT NULL,
    rush_attempts           INT DEFAULT NULL,
    rush_yards              FLOAT DEFAULT NULL,
    rush_touchdowns         INT DEFAULT NULL,
    pass_touchdowns         INT DEFAULT NULL,
    fantasy_points_actual   FLOAT DEFAULT NULL,
    fantasy_points_expected FLOAT DEFAULT NULL,
    fantasy_points_diff     FLOAT DEFAULT NULL,
    rec_first_downs         INT DEFAULT NULL,
    rush_first_downs        INT DEFAULT NULL,
    PRIMARY KEY (player_game_log_id),
    UNIQUE KEY uq_player_game_log (gsis_id, season, week),
    INDEX ix_player_game_logs_gsis (gsis_id),
    INDEX ix_player_game_logs_season_week (season, week)
);
