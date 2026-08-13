-- [udfa-001] 2026-08-06: Allow fractional UDFA budgets and bid amounts.
-- The league rule is that a team's budget can carry a fractional remainder (from the 10% carryover,
-- e.g. $105 left over -> $10.50 carried -> $110.50 budget), and that fraction may only be applied to
-- one player. Both columns were INT, so a fractional budget could not be represented at all.
--
-- DECIMAL rather than FLOAT: settle_bids() detects ties with an exact `==` comparison of amounts
-- before falling through to waiver_order, and binary floats would make that unreliable.
--
-- Existing integer rows widen in place (100 -> 100.00), so no backfill is required.

ALTER TABLE BidBudget
    MODIFY COLUMN starting_balance DECIMAL(7,2) NOT NULL DEFAULT 100.00;

ALTER TABLE UDFABids
    MODIFY COLUMN amount DECIMAL(7,2) NOT NULL;
