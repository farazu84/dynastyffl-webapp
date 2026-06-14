-- [players-001] 2026-06-13: Widen Players external provider IDs from INT to BIGINT.
-- These are opaque IDs from third parties (oddsjam, opta, swish, etc.) and can exceed
-- a signed INT's max (2,147,483,647) — e.g. oddsjam_id 777167582332 — causing
-- "Out of range value for column 'oddsjam_id'" failures during the player sync, which
-- silently skips updating that player.

ALTER TABLE Players
    MODIFY COLUMN espn_id BIGINT DEFAULT NULL,
    MODIFY COLUMN yahoo_id BIGINT DEFAULT NULL,
    MODIFY COLUMN fantasy_data_id BIGINT DEFAULT NULL,
    MODIFY COLUMN rotowire_id BIGINT DEFAULT NULL,
    MODIFY COLUMN rotoworld_id BIGINT DEFAULT NULL,
    MODIFY COLUMN stats_id BIGINT DEFAULT NULL,
    MODIFY COLUMN oddsjam_id BIGINT DEFAULT NULL,
    MODIFY COLUMN pandascore_id BIGINT DEFAULT NULL,
    MODIFY COLUMN opta_id BIGINT DEFAULT NULL,
    MODIFY COLUMN swish_id BIGINT DEFAULT NULL;
