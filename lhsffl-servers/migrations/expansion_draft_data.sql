-- [expansion-002] 2020 Expansion Draft data load.
-- Records the 48 expansion-draft selections (Tyler roster 10, Jacob roster 9) as both
-- DraftPicks(type='expansion') and Transactions(type='expansion') so trade-tree branches
-- terminate at the selection. Source of truth: the 2020-05-25 Sleeper commissioner adds to
-- rosters 9/10, cross-checked against EXPANSION DRAFT BOARD.pdf (pick order).
--
-- The expansion draft ran 24 rounds with 2 picks per round (Tyler + Jacob), so
--   round = ceil(pick_no / 2) and pick_no is the overall selection number (1-48).
--
-- 'atomic' picks (29): expansion txn carries the drop (the commissioner drop was never
--   ingested). 'pre-dropped' picks (19): the original team's free_agent drop is already in
--   Transactions, so the expansion txn is add-only.
--
-- Child rows resolve transaction_id via the unique sleeper_transaction_id
--   (= 920200000000 + pick_no), so this does not depend on auto-increment values.
-- Run once. Re-running fails on the UNIQUE sleeper_transaction_id (safe guard).

-- 0) Allow the new transaction type.
ALTER TABLE Transactions
    MODIFY COLUMN type ENUM('trade', 'waiver', 'free_agent', 'expansion') NOT NULL;

-- 1) Draft selections (48 rows): 24 rounds x 2 picks.
INSERT INTO DraftPicks
    (season, round, pick_no, draft_slot, drafting_roster_id, original_roster_id, player_sleeper_id, sleeper_draft_id, type)
VALUES
    (2020, 1, 1, 10, 10, 10, 4273, 920200000000, 'expansion'),  -- R 1 # 1 Chris Carson -> Tyler
    (2020, 1, 2, 9, 9, 9, 2320, 920200000000, 'expansion'),  -- R 1 # 2 Melvin Gordon -> Jacob
    (2020, 2, 3, 9, 9, 9, 3969, 920200000000, 'expansion'),  -- R 2 # 3 Leonard Fournette -> Jacob
    (2020, 2, 4, 10, 10, 10, 5848, 920200000000, 'expansion'),  -- R 2 # 4 Hollywood Brown -> Tyler
    (2020, 3, 5, 10, 10, 10, 2315, 920200000000, 'expansion'),  -- R 3 # 5 Todd Gurley -> Tyler
    (2020, 3, 6, 9, 9, 9, 4068, 920200000000, 'expansion'),  -- R 3 # 6 Mike Williams -> Jacob
    (2020, 4, 7, 9, 9, 9, 6789, 920200000000, 'expansion'),  -- R 4 # 7 Henry Ruggs -> Jacob
    (2020, 4, 8, 10, 10, 10, 6885, 920200000000, 'expansion'),  -- R 4 # 8 Keshaun vaughn -> Tyler
    (2020, 5, 9, 10, 10, 10, 1110, 920200000000, 'expansion'),  -- R 5 # 9 Ty hilton -> Tyler
    (2020, 5, 10, 9, 9, 9, 4152, 920200000000, 'expansion'),  -- R 5 #10 Marlon Mack -> Jacob
    (2020, 6, 11, 9, 9, 9, 6794, 920200000000, 'expansion'),  -- R 6 #11 Justin jefferson -> Jacob
    (2020, 6, 12, 10, 10, 10, 4082, 920200000000, 'expansion'),  -- R 6 #12 Curtis Samuel -> Tyler
    (2020, 7, 13, 10, 10, 10, 1067, 920200000000, 'expansion'),  -- R 7 #13 Marvin Jones -> Tyler
    (2020, 7, 14, 9, 9, 9, 5849, 920200000000, 'expansion'),  -- R 7 #14 Kyler Murray -> Jacob
    (2020, 8, 15, 9, 9, 9, 5022, 920200000000, 'expansion'),  -- R 8 #15 Dallas Goedert -> Jacob
    (2020, 8, 16, 10, 10, 10, 5170, 920200000000, 'expansion'),  -- R 8 #16 Phillip Lindsay -> Tyler
    (2020, 9, 17, 10, 10, 10, 3271, 920200000000, 'expansion'),  -- R 9 #17 Tyler Higbee -> Tyler
    (2020, 9, 18, 9, 9, 9, 6849, 920200000000, 'expansion'),  -- R 9 #18 Denzel Mims -> Jacob
    (2020, 10, 19, 9, 9, 9, 5000, 920200000000, 'expansion'),  -- R10 #19 Chase Edmunds -> Jacob
    (2020, 10, 20, 10, 10, 10, 4146, 920200000000, 'expansion'),  -- R10 #20 Dede Westbrook -> Tyler
    (2020, 11, 21, 10, 10, 10, 1833, 920200000000, 'expansion'),  -- R11 #21 Damien Williams -> Tyler
    (2020, 11, 22, 9, 9, 9, 2391, 920200000000, 'expansion'),  -- R11 #22 David Johnson -> Jacob
    (2020, 12, 23, 9, 9, 9, 4036, 920200000000, 'expansion'),  -- R12 #23 Corey Davis -> Jacob
    (2020, 12, 24, 10, 10, 10, 642, 920200000000, 'expansion'),  -- R12 #24 Golden tate -> Tyler
    (2020, 13, 25, 10, 10, 10, 5870, 920200000000, 'expansion'),  -- R13 #25 Daniel Jones -> Tyler
    (2020, 13, 26, 9, 9, 9, 6126, 920200000000, 'expansion'),  -- R13 #26 Irv smith jr. -> Jacob
    (2020, 14, 27, 9, 9, 9, 1264, 920200000000, 'expansion'),  -- R14 #27 Justin Tucker -> Jacob
    (2020, 14, 28, 10, 10, 10, 2331, 920200000000, 'expansion'),  -- R14 #28 Breshad Perrimen -> Tyler
    (2020, 15, 29, 10, 10, 10, 96, 920200000000, 'expansion'),  -- R15 #29 Aaron rodgers -> Tyler
    (2020, 15, 30, 9, 9, 9, 5955, 920200000000, 'expansion'),  -- R15 #30 Hunter renfrow -> Jacob
    (2020, 16, 31, 9, 9, 9, 2378, 920200000000, 'expansion'),  -- R16 #31 Tevin Coleman -> Jacob
    (2020, 16, 32, 10, 10, 10, 4949, 920200000000, 'expansion'),  -- R16 #32 Derrius Guice -> Tyler
    (2020, 17, 33, 10, 10, 10, 5185, 920200000000, 'expansion'),  -- R17 #33 Allen Lazard -> Tyler
    (2020, 17, 34, 9, 9, 9, 4985, 920200000000, 'expansion'),  -- R17 #34 Rashaad penny -> Jacob
    (2020, 18, 35, 9, 9, 9, 5122, 920200000000, 'expansion'),  -- R18 #35 Boston Scott -> Jacob
    (2020, 18, 36, 10, 10, 10, 3678, 920200000000, 'expansion'),  -- R18 #36 Will Lutz -> Tyler
    (2020, 19, 37, 10, 10, 10, 5889, 920200000000, 'expansion'),  -- R19 #37 Bryce Love -> Tyler
    (2020, 19, 38, 9, 9, 9, 4892, 920200000000, 'expansion'),  -- R19 #38 Baker Mayfield -> Jacob
    (2020, 20, 39, 9, 9, 9, 2382, 920200000000, 'expansion'),  -- R20 #39 Duke Johnson -> Jacob
    (2020, 20, 40, 10, 10, 10, 24, 920200000000, 'expansion'),  -- R20 #40 Matt Ryan -> Tyler
    (2020, 21, 41, 10, 10, 10, 5973, 920200000000, 'expansion'),  -- R21 #41 Josh Oliver -> Tyler
    (2020, 21, 42, 9, 9, 9, 367, 920200000000, 'expansion'),  -- R21 #42 Jared cook -> Jacob
    (2020, 22, 43, 9, 9, 9, 5915, 920200000000, 'expansion'),  -- R22 #43 Andy Isabella -> Jacob
    (2020, 22, 44, 10, 10, 10, 223, 920200000000, 'expansion'),  -- R22 #44 Larry Fitzgerald -> Tyler
    (2020, 23, 45, 10, 10, 10, 928, 920200000000, 'expansion'),  -- R23 #45 Randall cobb -> Tyler
    (2020, 23, 46, 9, 9, 9, 6951, 920200000000, 'expansion'),  -- R23 #46 Eno Benjamin -> Jacob
    (2020, 24, 47, 9, 9, 9, 6866, 920200000000, 'expansion'),  -- R24 #47 Kj Hill -> Jacob
    (2020, 24, 48, 10, 10, 10, 6824, 920200000000, 'expansion');  -- R24 #48 Donovan peoples jones -> Tyler

-- 2) Expansion transactions (48 rows), one per selection.
INSERT INTO Transactions
    (sleeper_transaction_id, year, week, type, status, sleeper_league_id, created_at, status_updated_at)
VALUES
    (920200000001, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- # 1 Chris Carson
    (920200000002, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- # 2 Melvin Gordon
    (920200000003, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- # 3 Leonard Fournette
    (920200000004, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- # 4 Hollywood Brown
    (920200000005, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- # 5 Todd Gurley
    (920200000006, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- # 6 Mike Williams
    (920200000007, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- # 7 Henry Ruggs
    (920200000008, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- # 8 Keshaun vaughn
    (920200000009, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- # 9 Ty hilton
    (920200000010, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #10 Marlon Mack
    (920200000011, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #11 Justin jefferson
    (920200000012, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #12 Curtis Samuel
    (920200000013, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #13 Marvin Jones
    (920200000014, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #14 Kyler Murray
    (920200000015, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #15 Dallas Goedert
    (920200000016, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #16 Phillip Lindsay
    (920200000017, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #17 Tyler Higbee
    (920200000018, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #18 Denzel Mims
    (920200000019, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #19 Chase Edmunds
    (920200000020, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #20 Dede Westbrook
    (920200000021, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #21 Damien Williams
    (920200000022, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #22 David Johnson
    (920200000023, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #23 Corey Davis
    (920200000024, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #24 Golden tate
    (920200000025, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #25 Daniel Jones
    (920200000026, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #26 Irv smith jr.
    (920200000027, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #27 Justin Tucker
    (920200000028, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #28 Breshad Perrimen
    (920200000029, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #29 Aaron rodgers
    (920200000030, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #30 Hunter renfrow
    (920200000031, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #31 Tevin Coleman
    (920200000032, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #32 Derrius Guice
    (920200000033, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #33 Allen Lazard
    (920200000034, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #34 Rashaad penny
    (920200000035, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #35 Boston Scott
    (920200000036, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #36 Will Lutz
    (920200000037, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #37 Bryce Love
    (920200000038, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #38 Baker Mayfield
    (920200000039, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #39 Duke Johnson
    (920200000040, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #40 Matt Ryan
    (920200000041, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #41 Josh Oliver
    (920200000042, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #42 Jared cook
    (920200000043, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #43 Andy Isabella
    (920200000044, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #44 Larry Fitzgerald
    (920200000045, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #45 Randall cobb
    (920200000046, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #46 Eno Benjamin
    (920200000047, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00'),  -- #47 Kj Hill
    (920200000048, 2020, 0, 'expansion', 'complete', 516385651688570880, '2020-05-25 00:00:00', '2020-05-25 00:00:00');  -- #48 Donovan peoples jones

-- 3) Player moves: an 'add' to the selecting team for every pick, plus a 'drop' from the
--    original team for the 29 atomic picks (pre-dropped picks already have a free_agent drop).
INSERT INTO TransactionPlayers (transaction_id, player_sleeper_id, sleeper_roster_id, action)
VALUES
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000001), 4273, 10, 'add'),  -- # 1 Chris Carson add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000002), 2320, 9, 'add'),  -- # 2 Melvin Gordon add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000002), 2320, 1, 'drop'),  -- # 2 Melvin Gordon drop <- r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000003), 3969, 9, 'add'),  -- # 3 Leonard Fournette add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000004), 5848, 10, 'add'),  -- # 4 Hollywood Brown add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000005), 2315, 10, 'add'),  -- # 5 Todd Gurley add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000005), 2315, 3, 'drop'),  -- # 5 Todd Gurley drop <- r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000006), 4068, 9, 'add'),  -- # 6 Mike Williams add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000006), 4068, 1, 'drop'),  -- # 6 Mike Williams drop <- r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000007), 6789, 9, 'add'),  -- # 7 Henry Ruggs add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000008), 6885, 10, 'add'),  -- # 8 Keshaun vaughn add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000008), 6885, 5, 'drop'),  -- # 8 Keshaun vaughn drop <- r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000009), 1110, 10, 'add'),  -- # 9 Ty hilton add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000009), 1110, 7, 'drop'),  -- # 9 Ty hilton drop <- r7
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000010), 4152, 9, 'add'),  -- #10 Marlon Mack add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000010), 4152, 5, 'drop'),  -- #10 Marlon Mack drop <- r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000011), 6794, 9, 'add'),  -- #11 Justin jefferson add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000011), 6794, 6, 'drop'),  -- #11 Justin jefferson drop <- r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000012), 4082, 10, 'add'),  -- #12 Curtis Samuel add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000013), 1067, 10, 'add'),  -- #13 Marvin Jones add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000013), 1067, 7, 'drop'),  -- #13 Marvin Jones drop <- r7
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000014), 5849, 9, 'add'),  -- #14 Kyler Murray add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000015), 5022, 9, 'add'),  -- #15 Dallas Goedert add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000016), 5170, 10, 'add'),  -- #16 Phillip Lindsay add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000016), 5170, 1, 'drop'),  -- #16 Phillip Lindsay drop <- r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000017), 3271, 10, 'add'),  -- #17 Tyler Higbee add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000017), 3271, 7, 'drop'),  -- #17 Tyler Higbee drop <- r7
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000018), 6849, 9, 'add'),  -- #18 Denzel Mims add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000018), 6849, 3, 'drop'),  -- #18 Denzel Mims drop <- r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000019), 5000, 9, 'add'),  -- #19 Chase Edmunds add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000020), 4146, 10, 'add'),  -- #20 Dede Westbrook add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000021), 1833, 10, 'add'),  -- #21 Damien Williams add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000022), 2391, 9, 'add'),  -- #22 David Johnson add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000023), 4036, 9, 'add'),  -- #23 Corey Davis add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000024), 642, 10, 'add'),  -- #24 Golden tate add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000024), 642, 6, 'drop'),  -- #24 Golden tate drop <- r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000025), 5870, 10, 'add'),  -- #25 Daniel Jones add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000025), 5870, 5, 'drop'),  -- #25 Daniel Jones drop <- r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000026), 6126, 9, 'add'),  -- #26 Irv smith jr. add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000026), 6126, 6, 'drop'),  -- #26 Irv smith jr. drop <- r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000027), 1264, 9, 'add'),  -- #27 Justin Tucker add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000028), 2331, 10, 'add'),  -- #28 Breshad Perrimen add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000028), 2331, 6, 'drop'),  -- #28 Breshad Perrimen drop <- r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000029), 96, 10, 'add'),  -- #29 Aaron rodgers add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000030), 5955, 9, 'add'),  -- #30 Hunter renfrow add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000031), 2378, 9, 'add'),  -- #31 Tevin Coleman add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000032), 4949, 10, 'add'),  -- #32 Derrius Guice add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000032), 4949, 3, 'drop'),  -- #32 Derrius Guice drop <- r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000033), 5185, 10, 'add'),  -- #33 Allen Lazard add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000034), 4985, 9, 'add'),  -- #34 Rashaad penny add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000035), 5122, 9, 'add'),  -- #35 Boston Scott add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000036), 3678, 10, 'add'),  -- #36 Will Lutz add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000036), 3678, 7, 'drop'),  -- #36 Will Lutz drop <- r7
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000037), 5889, 10, 'add'),  -- #37 Bryce Love add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000037), 5889, 2, 'drop'),  -- #37 Bryce Love drop <- r2
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000038), 4892, 9, 'add'),  -- #38 Baker Mayfield add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000038), 4892, 1, 'drop'),  -- #38 Baker Mayfield drop <- r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000039), 2382, 9, 'add'),  -- #39 Duke Johnson add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000039), 2382, 5, 'drop'),  -- #39 Duke Johnson drop <- r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000040), 24, 10, 'add'),  -- #40 Matt Ryan add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000040), 24, 1, 'drop'),  -- #40 Matt Ryan drop <- r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000041), 5973, 10, 'add'),  -- #41 Josh Oliver add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000041), 5973, 1, 'drop'),  -- #41 Josh Oliver drop <- r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000042), 367, 9, 'add'),  -- #42 Jared cook add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000042), 367, 1, 'drop'),  -- #42 Jared cook drop <- r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000043), 5915, 9, 'add'),  -- #43 Andy Isabella add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000043), 5915, 5, 'drop'),  -- #43 Andy Isabella drop <- r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000044), 223, 10, 'add'),  -- #44 Larry Fitzgerald add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000044), 223, 5, 'drop'),  -- #44 Larry Fitzgerald drop <- r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000045), 928, 10, 'add'),  -- #45 Randall cobb add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000045), 928, 3, 'drop'),  -- #45 Randall cobb drop <- r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000046), 6951, 9, 'add'),  -- #46 Eno Benjamin add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000046), 6951, 3, 'drop'),  -- #46 Eno Benjamin drop <- r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000047), 6866, 9, 'add'),  -- #47 Kj Hill add -> r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000047), 6866, 6, 'drop'),  -- #47 Kj Hill drop <- r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000048), 6824, 10, 'add'),  -- #48 Donovan peoples jones add -> r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000048), 6824, 7, 'drop');  -- #48 Donovan peoples jones drop <- r7

-- 4) Roster involvement: the selecting team for every pick, plus the original team for atomic picks.
INSERT INTO TransactionRosters (transaction_id, sleeper_roster_id, is_consenter)
VALUES
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000001), 10, 0),  -- # 1 Chris Carson selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000002), 9, 0),  -- # 2 Melvin Gordon selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000002), 1, 0),  -- # 2 Melvin Gordon original r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000003), 9, 0),  -- # 3 Leonard Fournette selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000004), 10, 0),  -- # 4 Hollywood Brown selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000005), 10, 0),  -- # 5 Todd Gurley selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000005), 3, 0),  -- # 5 Todd Gurley original r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000006), 9, 0),  -- # 6 Mike Williams selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000006), 1, 0),  -- # 6 Mike Williams original r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000007), 9, 0),  -- # 7 Henry Ruggs selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000008), 10, 0),  -- # 8 Keshaun vaughn selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000008), 5, 0),  -- # 8 Keshaun vaughn original r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000009), 10, 0),  -- # 9 Ty hilton selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000009), 7, 0),  -- # 9 Ty hilton original r7
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000010), 9, 0),  -- #10 Marlon Mack selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000010), 5, 0),  -- #10 Marlon Mack original r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000011), 9, 0),  -- #11 Justin jefferson selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000011), 6, 0),  -- #11 Justin jefferson original r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000012), 10, 0),  -- #12 Curtis Samuel selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000013), 10, 0),  -- #13 Marvin Jones selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000013), 7, 0),  -- #13 Marvin Jones original r7
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000014), 9, 0),  -- #14 Kyler Murray selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000015), 9, 0),  -- #15 Dallas Goedert selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000016), 10, 0),  -- #16 Phillip Lindsay selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000016), 1, 0),  -- #16 Phillip Lindsay original r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000017), 10, 0),  -- #17 Tyler Higbee selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000017), 7, 0),  -- #17 Tyler Higbee original r7
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000018), 9, 0),  -- #18 Denzel Mims selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000018), 3, 0),  -- #18 Denzel Mims original r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000019), 9, 0),  -- #19 Chase Edmunds selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000020), 10, 0),  -- #20 Dede Westbrook selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000021), 10, 0),  -- #21 Damien Williams selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000022), 9, 0),  -- #22 David Johnson selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000023), 9, 0),  -- #23 Corey Davis selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000024), 10, 0),  -- #24 Golden tate selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000024), 6, 0),  -- #24 Golden tate original r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000025), 10, 0),  -- #25 Daniel Jones selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000025), 5, 0),  -- #25 Daniel Jones original r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000026), 9, 0),  -- #26 Irv smith jr. selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000026), 6, 0),  -- #26 Irv smith jr. original r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000027), 9, 0),  -- #27 Justin Tucker selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000028), 10, 0),  -- #28 Breshad Perrimen selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000028), 6, 0),  -- #28 Breshad Perrimen original r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000029), 10, 0),  -- #29 Aaron rodgers selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000030), 9, 0),  -- #30 Hunter renfrow selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000031), 9, 0),  -- #31 Tevin Coleman selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000032), 10, 0),  -- #32 Derrius Guice selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000032), 3, 0),  -- #32 Derrius Guice original r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000033), 10, 0),  -- #33 Allen Lazard selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000034), 9, 0),  -- #34 Rashaad penny selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000035), 9, 0),  -- #35 Boston Scott selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000036), 10, 0),  -- #36 Will Lutz selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000036), 7, 0),  -- #36 Will Lutz original r7
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000037), 10, 0),  -- #37 Bryce Love selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000037), 2, 0),  -- #37 Bryce Love original r2
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000038), 9, 0),  -- #38 Baker Mayfield selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000038), 1, 0),  -- #38 Baker Mayfield original r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000039), 9, 0),  -- #39 Duke Johnson selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000039), 5, 0),  -- #39 Duke Johnson original r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000040), 10, 0),  -- #40 Matt Ryan selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000040), 1, 0),  -- #40 Matt Ryan original r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000041), 10, 0),  -- #41 Josh Oliver selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000041), 1, 0),  -- #41 Josh Oliver original r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000042), 9, 0),  -- #42 Jared cook selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000042), 1, 0),  -- #42 Jared cook original r1
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000043), 9, 0),  -- #43 Andy Isabella selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000043), 5, 0),  -- #43 Andy Isabella original r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000044), 10, 0),  -- #44 Larry Fitzgerald selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000044), 5, 0),  -- #44 Larry Fitzgerald original r5
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000045), 10, 0),  -- #45 Randall cobb selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000045), 3, 0),  -- #45 Randall cobb original r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000046), 9, 0),  -- #46 Eno Benjamin selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000046), 3, 0),  -- #46 Eno Benjamin original r3
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000047), 9, 0),  -- #47 Kj Hill selecting r9
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000047), 6, 0),  -- #47 Kj Hill original r6
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000048), 10, 0),  -- #48 Donovan peoples jones selecting r10
    ((SELECT transaction_id FROM Transactions WHERE sleeper_transaction_id = 920200000048), 7, 0);  -- #48 Donovan peoples jones original r7

