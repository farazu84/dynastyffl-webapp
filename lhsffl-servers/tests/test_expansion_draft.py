"""
Tests for the 2020 Expansion Draft trade-tree integration.

Coverage
────────
  app.logic.transaction_queries.get_full_trade_tree()  – expansion_selections map + the
                                                          "feeding drop" relabel logic
  app.scripts.backfill_expansion_draft._resolve_board_ids()  – all 48 board names resolve

Two structural cases are exercised (mirroring the real Sleeper data):
  • "atomic"      – the expansion txn itself carries the drop (←original team).
  • "pre-dropped" – the original team dropped the player in a separate free_agent txn that is
                    already ingested; the expansion txn is add-only. The feeding drop is the
                    free_agent one, and that is what must be relabeled as the selection.

Plus a date-guard case: a genuine post-expansion drop of an expansion player must NOT be
relabeled as a selection.
"""
from datetime import datetime

from tests.conftest import (
    make_team, make_player, make_transaction, make_roster, make_player_move, make_draft_pick,
)
from app.logic.transaction_queries import get_full_trade_tree


def _branch_txn_ids(teams_data, roster_id):
    return [t['transaction_id'] for t in teams_data[roster_id]['transactions']]


class TestExpansionTradeTree:
    def test_atomic_selection_terminates_branch(self, db):
        # Team 1 acquires Chris Carson in a trade, then he is taken in the expansion draft by
        # roster 9 (Jacob) via an atomic expansion txn (add to 9 + drop from 1 in one txn).
        make_team(db, team_id=1, sleeper_roster_id=1, team_name='Team 1')
        make_team(db, team_id=2, sleeper_roster_id=2, team_name='Team 2')
        make_team(db, team_id=9, sleeper_roster_id=9, team_name='Gizmart')
        make_player(db, player_id=101, sleeper_id=101, first_name='Chris', last_name='Carson', position='RB')

        make_transaction(db, transaction_id=1, txn_type='trade', created_at=datetime(2020, 1, 1))
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_player_move(db, 1, 101, 1, 'add')
        make_player_move(db, 1, 101, 2, 'drop')

        make_transaction(db, transaction_id=2, txn_type='expansion', created_at=datetime(2020, 5, 25))
        make_roster(db, 2, 1)
        make_roster(db, 2, 9)
        make_player_move(db, 2, 101, 9, 'add')
        make_player_move(db, 2, 101, 1, 'drop')
        make_draft_pick(db, season=2020, round_=1, original_roster_id=9, pick_no=1,
                        player_sleeper_id=101, type_='expansion')
        db.session.commit()

        origin, teams_data, _pick_meta, expansion_selections = get_full_trade_tree(1)
        assert origin is not None

        # Feeding drop is the expansion txn (id 2).
        assert '2:101' in expansion_selections
        sel = expansion_selections['2:101']
        assert sel['team_name'] == 'Gizmart'
        assert sel['round'] == 1
        assert sel['pick_no'] == 1

        # Team 1's branch terminates at the expansion txn.
        assert 2 in _branch_txn_ids(teams_data, 1)

    def test_pre_dropped_selection_uses_free_agent_drop(self, db):
        # Team 1 acquires Hollywood Brown, then DROPS him via a free_agent txn (already ingested),
        # then an add-only expansion txn moves him to roster 10 (Tyler).
        make_team(db, team_id=1, sleeper_roster_id=1, team_name='Team 1')
        make_team(db, team_id=2, sleeper_roster_id=2, team_name='Team 2')
        make_team(db, team_id=10, sleeper_roster_id=10, team_name="Tyler's Team")
        make_player(db, player_id=102, sleeper_id=102, first_name='Hollywood', last_name='Brown', position='WR')

        make_transaction(db, transaction_id=1, txn_type='trade', created_at=datetime(2020, 1, 1))
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_player_move(db, 1, 102, 1, 'add')
        make_player_move(db, 1, 102, 2, 'drop')

        # Add-only expansion txn, stamped at MIDNIGHT (as the data migration does)...
        make_transaction(db, transaction_id=3, txn_type='expansion', created_at=datetime(2020, 5, 25, 0, 0))
        make_roster(db, 3, 10)
        make_player_move(db, 3, 102, 10, 'add')
        make_draft_pick(db, season=2020, round_=1, original_roster_id=10, pick_no=4,
                        player_sleeper_id=102, type_='expansion')

        # ...while the real feeding free_agent drop happens LATER that same day (the case that
        # broke when the cutoff compared exact timestamps instead of the day).
        make_transaction(db, transaction_id=2, txn_type='free_agent', created_at=datetime(2020, 5, 25, 14, 0))
        make_roster(db, 2, 1)
        make_player_move(db, 2, 102, 1, 'drop')
        db.session.commit()

        _origin, teams_data, _pick_meta, expansion_selections = get_full_trade_tree(1)

        # The free_agent drop (id 2) is the feeding drop — not the add-only expansion txn (id 3).
        assert '2:102' in expansion_selections
        assert '3:102' not in expansion_selections
        assert expansion_selections['2:102']['team_name'] == "Tyler's Team"

        # Team 1's branch terminates at the free_agent drop.
        assert 2 in _branch_txn_ids(teams_data, 1)

    def test_post_expansion_drop_not_relabeled(self, db):
        # Player taken in expansion by roster 10, later traded to team 2, who then cuts him in
        # 2021. That later free_agent drop must NOT be relabeled as the expansion selection.
        make_team(db, team_id=1, sleeper_roster_id=1, team_name='Team 1')
        make_team(db, team_id=2, sleeper_roster_id=2, team_name='Team 2')
        make_team(db, team_id=10, sleeper_roster_id=10, team_name="Tyler's Team")
        make_player(db, player_id=103, sleeper_id=103, first_name='Some', last_name='Player', position='WR')

        # Atomic expansion: dropped from team 1, added to roster 10.
        make_transaction(db, transaction_id=1, txn_type='expansion', created_at=datetime(2020, 5, 25))
        make_roster(db, 1, 1)
        make_roster(db, 1, 10)
        make_player_move(db, 1, 103, 10, 'add')
        make_player_move(db, 1, 103, 1, 'drop')
        make_draft_pick(db, season=2020, round_=1, original_roster_id=10, pick_no=5,
                        player_sleeper_id=103, type_='expansion')

        # Origin trade we view: roster 10 trades the player to team 2 (2021).
        make_transaction(db, transaction_id=2, txn_type='trade', created_at=datetime(2021, 1, 1))
        make_roster(db, 2, 10)
        make_roster(db, 2, 2)
        make_player_move(db, 2, 103, 2, 'add')
        make_player_move(db, 2, 103, 10, 'drop')

        # Post-expansion cut by team 2.
        make_transaction(db, transaction_id=3, txn_type='free_agent', created_at=datetime(2021, 6, 1))
        make_roster(db, 3, 2)
        make_player_move(db, 3, 103, 2, 'drop')
        db.session.commit()

        _origin, _teams_data, _pick_meta, expansion_selections = get_full_trade_tree(2)

        # Feeding drop is the 2020 expansion txn (id 1); the 2021 cut (id 3) is left alone.
        assert '1:103' in expansion_selections
        assert '3:103' not in expansion_selections


class TestExpansionBackfillResolution:
    def test_all_48_board_names_resolve(self):
        from app.scripts.backfill_expansion_draft import _resolve_board_ids, BOARD
        resolved = _resolve_board_ids()
        assert len(resolved) == len(BOARD) == 48
        assert all(pick_no in resolved for pick_no, _name, _drafter in BOARD)
