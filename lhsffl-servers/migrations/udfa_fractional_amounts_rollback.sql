-- [udfa-001-rollback] Undo the fractional UDFA amounts migration.
--
-- WARNING: this is lossy. Any budget or bid holding cents will be rounded to a whole dollar by
-- MySQL when the column narrows back to INT — a $100.50 winning bid becomes $101, which changes
-- settlement outcomes. Check for fractional rows before running this:
--
--   SELECT bid_budget_id, team_id, year, starting_balance FROM BidBudget
--   WHERE starting_balance <> FLOOR(starting_balance);
--
--   SELECT bid_id, team_id, year, amount FROM UDFABids
--   WHERE amount <> FLOOR(amount);

ALTER TABLE BidBudget
    MODIFY COLUMN starting_balance INT NOT NULL DEFAULT 100;

ALTER TABLE UDFABids
    MODIFY COLUMN amount INT NOT NULL;
