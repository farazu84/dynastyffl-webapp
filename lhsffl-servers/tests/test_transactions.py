"""
Tests for /v1/transactions endpoints.

Coverage:
  GET /v1/transactions                           – filtered list
  GET /v1/transactions/<id>                      – single transaction
  GET /v1/transactions/week/<n>                  – by week
  GET /v1/transactions/team/<id>                 – team transactions
  GET /v1/transactions/team/<id>/trades          – team trades only
  GET /v1/transactions/trades/random             – random trades
  GET /v1/transactions/trade-tree/<player_id>    – player trade tree
  GET /v1/transactions/<id>/full_trade_tree      – full ripple-effect tree

Fixture strategy:
  • `league` fixture  – seeds a standard 4-team league (see conftest.create_league)
  • @with_trade(...)  – decorator that creates a trade + rosters + player/pick moves
  • @with_waiver(...) – decorator that creates a waiver claim
  • @with_draft_pick  – decorator that creates a DraftPicks row
  Simple tests that only need a single row still call make_* helpers directly.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from tests.conftest import (
    create_league,
    make_team, make_player, make_transaction, make_roster,
    make_player_move, make_pick_move, make_draft_pick, make_league_state,
    with_trade, with_waiver, with_draft_pick, create_resource,
)


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions  (filtered list)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTransactions:
    """
    The league fixture gives us 4 teams (roster_ids 1-4) and 20 players
    (sleeper_ids 101-120). Individual tests add the transactions they need.
    """

    @with_trade(name='t1', roster_ids=[1, 2], adds={1: [101], 2: [102]}, year=2024, week=3)
    @with_waiver(name='w1', roster_id=1, add=103, year=2024, week=4)
    @with_waiver(name='fa', roster_id=2, add=104, year=2023, week=1)
    @with_trade(name='pending', roster_ids=[1, 2], year=2024, week=3, status='pending')
    def test_no_filters_returns_all_complete(self, client, db, league, t1, w1, fa, pending):
        r = client.get('/v1/transactions')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        # 3 complete (t1, w1, fa) – pending excluded
        assert len(data['transactions']) == 3

    @with_trade(name='trade_2024', roster_ids=[1, 2], year=2024, week=3)
    @with_waiver(name='waiver_2023', roster_id=1, year=2023, week=1)
    def test_filter_by_year(self, client, db, league, trade_2024, waiver_2023):
        r = client.get('/v1/transactions?year=2024')
        data = r.get_json()
        assert r.status_code == 200
        assert all(t['year'] == 2024 for t in data['transactions'])
        assert len(data['transactions']) == 1

    @with_trade(name='wk3', roster_ids=[1, 2], year=2024, week=3)
    @with_waiver(name='wk4', roster_id=1, year=2024, week=4)
    def test_filter_by_week(self, client, db, league, wk3, wk4):
        r = client.get('/v1/transactions?week=3')
        data = r.get_json()
        assert r.status_code == 200
        assert all(t['week'] == 3 for t in data['transactions'])
        assert len(data['transactions']) == 1

    @with_trade(name='trade', roster_ids=[1, 2])
    @with_waiver(name='waiver', roster_id=1)
    def test_filter_by_type_trade(self, client, db, league, trade, waiver):
        r = client.get('/v1/transactions?type=trade')
        data = r.get_json()
        assert r.status_code == 200
        assert all(t['type'] == 'trade' for t in data['transactions'])
        assert len(data['transactions']) == 1

    @with_trade(name='trade', roster_ids=[1, 2])
    @with_waiver(name='waiver', roster_id=1)
    def test_filter_by_type_waiver(self, client, db, league, trade, waiver):
        r = client.get('/v1/transactions?type=waiver')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['type'] == 'waiver'

    @create_resource('Transactions',
                     sleeper_transaction_id=20001, type='free_agent', status='complete',
                     year=2024, week=1, sleeper_league_id=999, created_at=datetime(2024, 9, 1))
    @create_resource('Transactions',
                     sleeper_transaction_id=20002, type='trade', status='complete',
                     year=2024, week=1, sleeper_league_id=999, created_at=datetime(2024, 9, 2))
    def test_filter_by_type_free_agent(self, client, db, league):
        r = client.get('/v1/transactions?type=free_agent')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['type'] == 'free_agent'

    @with_trade(name='trade', roster_ids=[1, 2], year=2024, week=3)
    @with_waiver(name='waiver', roster_id=1, year=2024, week=4)
    def test_combined_filters(self, client, db, league, trade, waiver):
        r = client.get('/v1/transactions?year=2024&type=trade')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['type'] == 'trade'
        assert data['transactions'][0]['year'] == 2024

    @with_trade(name='trade', roster_ids=[1, 2], year=2024)
    def test_filters_with_no_matches_returns_empty(self, client, db, league, trade):
        r = client.get('/v1/transactions?year=1999')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    def test_empty_db_returns_empty_list(self, client, db):
        r = client.get('/v1/transactions')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    @with_trade(name='pending', roster_ids=[1, 2], status='pending')
    def test_pending_transactions_excluded(self, client, db, league, pending):
        r = client.get('/v1/transactions')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    @with_trade(name='t1', roster_ids=[1, 2])
    @with_waiver(name='w1', roster_id=1)
    def test_filter_by_roster_id(self, client, db, league, t1, w1):
        # Roster 1 is in both t1 (trade) and w1 (waiver)
        r = client.get('/v1/transactions?roster_id=1')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 2


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/<id>  (single transaction)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetSingleTransaction:

    @with_trade(roster_ids=[1, 2])
    def test_valid_id_returns_transaction(self, client, db, league, trade):
        r = client.get(f'/v1/transactions/{trade.transaction_id}')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        assert data['transaction']['transaction_id'] == trade.transaction_id
        assert data['transaction']['type'] == 'trade'

    def test_nonexistent_id_returns_404(self, client, db):
        r = client.get('/v1/transactions/9999')
        data = r.get_json()
        assert r.status_code == 404
        assert data['success'] is False
        assert 'not found' in data['error'].lower()

    @with_trade(roster_ids=[1, 2], status='pending')
    def test_pending_transaction_still_returned(self, client, db, league, trade):
        # Single-lookup endpoint does NOT filter by status
        r = client.get(f'/v1/transactions/{trade.transaction_id}')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transaction']['status'] == 'pending'

    @with_trade(roster_ids=[1, 2], adds={1: [101]})
    def test_transaction_includes_player_moves(self, client, db, league, trade):
        r = client.get(f'/v1/transactions/{trade.transaction_id}')
        data = r.get_json()
        assert r.status_code == 200
        moves = data['transaction']['player_moves']
        assert len(moves) == 1
        assert moves[0]['player_sleeper_id'] == 101
        assert moves[0]['action'] == 'add'


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/week/<n>  (by week, current year)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTransactionsByWeek:

    @with_trade(name='wk5a', roster_ids=[1, 2], year=2024, week=5)
    @with_waiver(name='wk5b', roster_id=1, year=2024, week=5)
    @with_trade(name='wk6',  roster_ids=[1, 2], year=2024, week=6)
    def test_valid_week_returns_matching_transactions(self, client, db, league, wk5a, wk5b, wk6):
        with patch('app.models.transactions.get_current_year', return_value=2024):
            r = client.get('/v1/transactions/week/5')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 2
        assert all(t['week'] == 5 for t in data['transactions'])

    @with_trade(roster_ids=[1, 2], year=2024, week=3)
    def test_week_with_no_transactions_returns_empty(self, client, db, league, trade):
        with patch('app.models.transactions.get_current_year', return_value=2024):
            r = client.get('/v1/transactions/week/99')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    @with_trade(name='old', roster_ids=[1, 2], year=2023, week=5)
    @with_trade(name='cur', roster_ids=[1, 2], year=2024, week=5)
    def test_week_filters_by_current_year_only(self, client, db, league, old, cur):
        with patch('app.models.transactions.get_current_year', return_value=2024):
            r = client.get('/v1/transactions/week/5')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['year'] == 2024

    @with_trade(roster_ids=[1, 2], year=2024, week=5, status='pending')
    def test_week_excludes_incomplete_transactions(self, client, db, league, trade):
        with patch('app.models.transactions.get_current_year', return_value=2024):
            r = client.get('/v1/transactions/week/5')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/team/<id>  (all transactions for a team)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTeamTransactions:

    @with_trade(name='trade', roster_ids=[1, 2])
    @with_waiver(name='waiver', roster_id=1)
    def test_valid_team_returns_all_types(self, client, db, league, trade, waiver):
        r = client.get('/v1/transactions/team/1')  # team_id=1 has roster_id=1
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        assert len(data['transactions']) == 2

    def test_nonexistent_team_returns_404(self, client, db):
        r = client.get('/v1/transactions/team/999')
        data = r.get_json()
        assert r.status_code == 404
        assert data['success'] is False

    def test_team_with_no_transactions_returns_empty(self, client, db, league):
        r = client.get('/v1/transactions/team/1')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    @with_trade(name='team1_trade', roster_ids=[1, 2])
    @with_trade(name='team2_only', roster_ids=[2, 3])
    def test_only_returns_transactions_for_that_team(self, client, db, league, team1_trade, team2_only):
        r = client.get('/v1/transactions/team/1')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['transaction_id'] == team1_trade.transaction_id

    @with_trade(name='complete', roster_ids=[1, 2])
    @with_trade(name='pending',  roster_ids=[1, 2], status='pending')
    def test_excludes_incomplete_transactions(self, client, db, league, complete, pending):
        r = client.get('/v1/transactions/team/1')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/team/<id>/trades  (trades only)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTeamTrades:

    @with_trade(roster_ids=[1, 2])
    @with_waiver(roster_id=1)
    def test_returns_only_trades(self, client, db, league, trade, waiver):
        r = client.get('/v1/transactions/team/1/trades')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['type'] == 'trade'

    @with_waiver(roster_id=1)
    def test_team_with_only_waivers_returns_empty(self, client, db, league, waiver):
        r = client.get('/v1/transactions/team/1/trades')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    def test_nonexistent_team_returns_404(self, client, db):
        r = client.get('/v1/transactions/team/999/trades')
        data = r.get_json()
        assert r.status_code == 404
        assert data['success'] is False


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/trades/random
# ═══════════════════════════════════════════════════════════════════════════

class TestGetRandomTrades:

    def test_returns_up_to_5_trades(self, client, db, league):
        for i in range(10):
            make_transaction(db, i + 1, txn_type='trade')
        db.session.commit()
        r = client.get('/v1/transactions/trades/random')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 5

    @with_trade(name='t1', roster_ids=[1, 2])
    @with_trade(name='t2', roster_ids=[1, 3])
    def test_returns_all_when_fewer_than_5(self, client, db, league, t1, t2):
        r = client.get('/v1/transactions/trades/random')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 2

    @with_waiver(roster_id=1)
    def test_no_trades_returns_empty(self, client, db, league, waiver):
        r = client.get('/v1/transactions/trades/random')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    @with_trade(name='pending', roster_ids=[1, 2], status='pending')
    @with_trade(name='complete', roster_ids=[1, 2], status='complete')
    def test_excludes_pending_trades(self, client, db, league, pending, complete):
        r = client.get('/v1/transactions/trades/random')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['status'] == 'complete'


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/trade-tree/<player_sleeper_id>
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTradeTree:

    @with_trade(roster_ids=[1, 2], adds={2: [101]})
    def test_player_with_trades_returns_info_and_tree(self, client, db, league, trade):
        r = client.get('/v1/transactions/trade-tree/101')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        assert data['player']['sleeper_id'] == 101
        assert len(data['trade_tree']) == 1

    @with_trade(roster_ids=[1, 2], adds={1: [999]})   # sleeper_id 999 has no Players row
    def test_player_not_in_players_table_returns_none_info(self, client, db, league, trade):
        r = client.get('/v1/transactions/trade-tree/999')
        data = r.get_json()
        assert r.status_code == 200
        assert data['player'] is None
        assert len(data['trade_tree']) == 1

    def test_player_with_no_moves_returns_empty_tree(self, client, db, league):
        # Player 101 exists in the league but has never been in a transaction
        r = client.get('/v1/transactions/trade-tree/101')
        data = r.get_json()
        assert r.status_code == 200
        assert data['player'] is None   # early-return before Players lookup
        assert data['trade_tree'] == []

    def test_completely_unknown_player_returns_empty(self, client, db):
        r = client.get('/v1/transactions/trade-tree/77777')
        data = r.get_json()
        assert r.status_code == 200
        assert data['player'] is None
        assert data['trade_tree'] == []

    @with_trade(name='complete', roster_ids=[1, 2], adds={1: [101]})
    @with_trade(name='pending',  roster_ids=[1, 2], adds={1: [101]}, status='pending')
    def test_only_complete_transactions_in_tree(self, client, db, league, complete, pending):
        r = client.get('/v1/transactions/trade-tree/101')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['trade_tree']) == 1
        assert data['trade_tree'][0]['status'] == 'complete'

    @with_trade(name='first',  roster_ids=[1, 2], adds={1: [101]},
                created_at=datetime(2024, 10, 5))
    @with_trade(name='second', roster_ids=[1, 2], drops={1: [101]},
                created_at=datetime(2024, 9, 1))
    def test_multiple_trades_returned_chronologically(self, client, db, league, first, second):
        r = client.get('/v1/transactions/trade-tree/101')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['trade_tree']) == 2
        dates = [t['created_at'] for t in data['trade_tree']]
        assert dates == sorted(dates)

    @with_trade(name='acquired', roster_ids=[1, 2], adds={1: [101]},
                created_at=datetime(2024, 9, 1))
    @with_trade(name='traded_away', roster_ids=[1, 3], drops={1: [101]},
                created_at=datetime(2024, 10, 1))
    def test_player_appears_in_add_and_drop(self, client, db, league, acquired, traded_away):
        r = client.get('/v1/transactions/trade-tree/101')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['trade_tree']) == 2


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/<id>/full_trade_tree
# ═══════════════════════════════════════════════════════════════════════════

class TestFullTradeTree:

    def test_nonexistent_transaction_returns_404(self, client, db):
        r = client.get('/v1/transactions/9999/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 404
        assert data['success'] is False

    @with_trade(roster_ids=[1, 2])          # no player/pick moves
    def test_transaction_with_no_moves_returns_empty_teams(self, client, db, league, trade):
        r = client.get(f'/v1/transactions/{trade.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        assert data['origin']['transaction_id'] == trade.transaction_id
        assert data['teams'] == {}
        assert data['pick_metadata'] == {}

    @with_trade(
        roster_ids=[1, 2],
        adds={1: [102], 2: [101]},
        drops={1: [101], 2: [102]},
    )
    def test_simple_player_trade_populates_both_teams(self, client, db, league, trade):
        """Roster 1 gets player 102; Roster 2 gets player 101."""
        r = client.get(f'/v1/transactions/{trade.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        teams = data['teams']
        assert '1' in teams and '2' in teams
        assert any(p['sleeper_id'] == 102 for p in teams['1']['acquired_players'])
        assert any(p['sleeper_id'] == 101 for p in teams['2']['acquired_players'])

    @with_trade(roster_ids=[99], adds={99: [101]})   # roster_id 99 has no Teams row
    def test_unknown_roster_falls_back_to_placeholder_name(self, client, db, league, trade):
        r = client.get(f'/v1/transactions/{trade.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        teams = data['teams']
        assert '99' in teams
        assert teams['99']['team_name'] == 'Roster 99'
        assert teams['99']['team_id'] is None

    @with_trade(
        name='origin',
        roster_ids=[1, 2],
        adds={1: [101], 2: [102]},
        drops={1: [102], 2: [101]},
        created_at=datetime(2024, 9, 1),
    )
    @with_trade(
        name='followup',
        roster_ids=[1, 3],
        adds={1: [103], 3: [101]},
        drops={1: [101], 3: [103]},
        created_at=datetime(2024, 9, 8),
    )
    def test_chained_trade_tracked_across_transactions(self, client, db, league, origin, followup):
        """
        Origin:  Roster 1 gets player 101 (101 tracked for roster 1).
        Followup: Roster 1 trades player 101 to Roster 3 → chain continues.

        Expected:
          teams['1']['acquired_players'] = [player 101]
          teams['1']['transactions']     = [followup]
          teams['2']['acquired_players'] = [player 102]
          teams['2']['transactions']     = []
          Roster 3 is NOT in origin branches → absent from teams.
        """
        r = client.get(f'/v1/transactions/{origin.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        teams = data['teams']

        assert any(p['sleeper_id'] == 101 for p in teams['1']['acquired_players'])
        assert len(teams['1']['transactions']) == 1
        assert teams['1']['transactions'][0]['transaction_id'] == followup.transaction_id

        assert any(p['sleeper_id'] == 102 for p in teams['2']['acquired_players'])
        assert teams['2']['transactions'] == []

        assert '3' not in teams

    @with_trade(
        name='origin',
        roster_ids=[1, 2],
        adds={1: [101]},
        created_at=datetime(2024, 9, 1),
    )
    @with_waiver(
        name='unrelated',
        roster_id=1,
        add=103,                          # 103 is not 101 → no tracked asset moved
        created_at=datetime(2024, 9, 5),
    )
    def test_future_unrelated_transaction_is_ignored(self, client, db, league, origin, unrelated):
        r = client.get(f'/v1/transactions/{origin.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        # Waiver didn't touch the tracked asset (101), so no chain transaction
        assert data['teams']['1']['transactions'] == []

    @with_trade(
        roster_ids=[1, 2],
        picks=[{'season': 2025, 'round': 2, 'roster_id': 2, 'owner_id': 1, 'previous_owner_id': 2}],
    )
    def test_pick_only_trade_populates_acquired_picks(self, client, db, league, trade):
        r = client.get(f'/v1/transactions/{trade.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        picks = data['teams']['1']['acquired_picks']
        assert len(picks) == 1
        assert picks[0]['season'] == 2025
        assert picks[0]['round'] == 2

    @with_trade(
        name='trade',
        roster_ids=[1, 2],
        picks=[{'season': 2023, 'round': 1, 'roster_id': 2, 'owner_id': 1, 'previous_owner_id': 2}],
    )
    @with_draft_pick(name='dp', season=2023, round=1, original_roster_id=2,
                     pick_no=1, player_sleeper_id=101)
    def test_pick_with_draft_result_shows_drafted_player(self, client, db, league, trade, dp):
        r = client.get(f'/v1/transactions/{trade.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        picks = data['teams']['1']['acquired_picks']
        assert picks[0]['pick_no'] == 1
        assert picks[0]['drafted_player']['sleeper_id'] == 101

        key = '2023:1:2'
        assert key in data['pick_metadata']
        assert data['pick_metadata'][key]['drafted_player']['sleeper_id'] == 101

    @with_trade(
        name='trade',
        roster_ids=[1, 2],
        picks=[{'season': 2023, 'round': 1, 'roster_id': 2, 'owner_id': 1, 'previous_owner_id': 2}],
    )
    @with_draft_pick(name='dp', season=2023, round=1, original_roster_id=2,
                     pick_no=3, player_sleeper_id=88888)   # 88888 has no Players row
    def test_pick_drafted_but_player_not_in_players_table(self, client, db, league, trade, dp):
        r = client.get(f'/v1/transactions/{trade.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        picks = data['teams']['1']['acquired_picks']
        assert picks[0]['pick_no'] == 3
        assert picks[0]['drafted_player'] is None

    @with_trade(
        roster_ids=[1, 2],
        picks=[{'season': 2026, 'round': 3, 'roster_id': 2, 'owner_id': 1, 'previous_owner_id': 2}],
    )
    def test_pick_not_yet_drafted_shows_none_player(self, client, db, league, trade):
        r = client.get(f'/v1/transactions/{trade.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        picks = data['teams']['1']['acquired_picks']
        assert picks[0]['pick_no'] is None
        assert picks[0]['drafted_player'] is None

    @with_trade(
        name='origin',
        roster_ids=[1, 2],
        adds={1: [101]},
        created_at=datetime(2024, 9, 1),
    )
    @with_waiver(
        name='waiver',
        roster_id=1,
        add=103,
        drop=101,                          # drops the tracked asset → chain continues
        created_at=datetime(2024, 9, 5),
    )
    def test_waiver_drop_of_acquired_player_tracked_in_chain(self, client, db, league, origin, waiver):
        r = client.get(f'/v1/transactions/{origin.transaction_id}/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['teams']['1']['transactions']) == 1
        assert data['teams']['1']['transactions'][0]['transaction_id'] == waiver.transaction_id
