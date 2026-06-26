-- [expansion-002-rollback] Undo the 2020 Expansion Draft data load.
-- Removes exactly the rows inserted by expansion_draft_data.sql, identified by the sentinels:
--   * expansion Transactions:  sleeper_transaction_id BETWEEN 920200000001 AND 920200000048
--   * expansion DraftPicks:    sleeper_draft_id = 920200000000
-- Children (TransactionPlayers / TransactionRosters) are deleted first while the parent
-- Transactions still exist (so the subquery can resolve them), then the Transactions, then the
-- DraftPicks, and finally the enum is reverted.

-- 1) Child rows of the expansion transactions.
DELETE FROM TransactionPlayers
WHERE transaction_id IN (
    SELECT transaction_id FROM Transactions
    WHERE sleeper_transaction_id BETWEEN 920200000001 AND 920200000048
);

DELETE FROM TransactionRosters
WHERE transaction_id IN (
    SELECT transaction_id FROM Transactions
    WHERE sleeper_transaction_id BETWEEN 920200000001 AND 920200000048
);

-- 2) The expansion transactions themselves.
DELETE FROM Transactions
WHERE sleeper_transaction_id BETWEEN 920200000001 AND 920200000048;

-- 3) The expansion draft selections.
DELETE FROM DraftPicks
WHERE sleeper_draft_id = 920200000000;

-- 4) Revert the enum (safe now that no expansion-typed rows remain).
ALTER TABLE Transactions
    MODIFY COLUMN type ENUM('trade', 'waiver', 'free_agent') NOT NULL;
