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
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from tests.conftest import (
    make_team, make_player, make_transaction, make_roster,
    make_player_move, make_pick_move, make_draft_pick, make_league_state,
)


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions  (filtered list)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTransactions:

    def _seed_mixed_transactions(self, db):
        """3 complete (trade/waiver/free_agent across years), 1 pending."""
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')

        make_transaction(db, 1, txn_type='trade',      year=2024, week=3)
        make_transaction(db, 2, txn_type='waiver',     year=2024, week=4)
        make_transaction(db, 3, txn_type='free_agent', year=2023, week=1)
        make_transaction(db, 4, txn_type='trade',      year=2024, week=3, status='pending')

        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_roster(db, 2, 1)
        make_roster(db, 3, 2)
        db.session.commit()

    def test_no_filters_returns_all_complete(self, client, db):
        self._seed_mixed_transactions(db)
        r = client.get('/v1/transactions')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        # 3 complete transactions; pending excluded
        assert len(data['transactions']) == 3

    def test_filter_by_year(self, client, db):
        self._seed_mixed_transactions(db)
        r = client.get('/v1/transactions?year=2024')
        data = r.get_json()
        assert r.status_code == 200
        years = [t['year'] for t in data['transactions']]
        assert all(y == 2024 for y in years)
        assert len(years) == 2  # txn 1 (trade) + txn 2 (waiver)

    def test_filter_by_week(self, client, db):
        self._seed_mixed_transactions(db)
        r = client.get('/v1/transactions?week=3')
        data = r.get_json()
        assert r.status_code == 200
        weeks = [t['week'] for t in data['transactions']]
        assert all(w == 3 for w in weeks)

    def test_filter_by_type_trade(self, client, db):
        self._seed_mixed_transactions(db)
        r = client.get('/v1/transactions?type=trade')
        data = r.get_json()
        assert r.status_code == 200
        types = [t['type'] for t in data['transactions']]
        assert all(tp == 'trade' for tp in types)
        # pending trade is excluded by status filter
        assert len(types) == 1

    def test_filter_by_type_waiver(self, client, db):
        self._seed_mixed_transactions(db)
        r = client.get('/v1/transactions?type=waiver')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['type'] == 'waiver'

    def test_filter_by_type_free_agent(self, client, db):
        self._seed_mixed_transactions(db)
        r = client.get('/v1/transactions?type=free_agent')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['type'] == 'free_agent'

    @pytest.mark.xfail(
        strict=True,
        raises=Exception,
        reason=(
            "Bug in Transactions.get_filtered: after query.join(TransactionRosters), "
            "the subsequent filter_by(status='complete') incorrectly targets the joined "
            "TransactionRosters entity (which has no 'status' column) instead of Transactions. "
            "Fix: replace filter_by(status='complete') with filter(Transactions.status == 'complete')."
        ),
    )
    def test_filter_by_roster_id(self, client, db):
        self._seed_mixed_transactions(db)
        # Only roster 1 is in txn 1 (trade) and txn 2 (waiver)
        r = client.get('/v1/transactions?roster_id=1')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 2

    def test_combined_filters(self, client, db):
        self._seed_mixed_transactions(db)
        r = client.get('/v1/transactions?year=2024&type=trade')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['type'] == 'trade'
        assert data['transactions'][0]['year'] == 2024

    def test_filters_with_no_matches_returns_empty(self, client, db):
        self._seed_mixed_transactions(db)
        r = client.get('/v1/transactions?year=1999')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    def test_pending_transactions_excluded(self, client, db):
        make_transaction(db, 10, status='pending')
        make_transaction(db, 11, status='failed')
        db.session.commit()
        r = client.get('/v1/transactions')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    def test_empty_db_returns_empty_list(self, client, db):
        r = client.get('/v1/transactions')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        assert data['transactions'] == []


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/<id>  (single transaction)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetSingleTransaction:

    def test_valid_id_returns_transaction(self, client, db):
        make_transaction(db, 1, txn_type='trade')
        db.session.commit()
        r = client.get('/v1/transactions/1')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        assert data['transaction']['transaction_id'] == 1
        assert data['transaction']['type'] == 'trade'

    def test_nonexistent_id_returns_404(self, client, db):
        r = client.get('/v1/transactions/9999')
        data = r.get_json()
        assert r.status_code == 404
        assert data['success'] is False
        assert 'not found' in data['error'].lower()

    def test_pending_transaction_still_returned(self, client, db):
        # Single-lookup endpoint does NOT filter by status
        make_transaction(db, 5, status='pending')
        db.session.commit()
        r = client.get('/v1/transactions/5')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transaction']['status'] == 'pending'

    def test_transaction_includes_player_moves(self, client, db):
        make_player(db, 1, 100, 'Patrick', 'Mahomes', 'QB')
        make_transaction(db, 1, txn_type='waiver')
        make_player_move(db, 1, 100, 1, 'add')
        db.session.commit()
        r = client.get('/v1/transactions/1')
        data = r.get_json()
        assert r.status_code == 200
        moves = data['transaction']['player_moves']
        assert len(moves) == 1
        assert moves[0]['player_sleeper_id'] == 100
        assert moves[0]['action'] == 'add'


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/week/<n>  (by week, current year)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTransactionsByWeek:

    def test_valid_week_returns_matching_transactions(self, client, db):
        # League defaults to year=2024 when no LeagueState row exists
        make_transaction(db, 1, year=2024, week=5)
        make_transaction(db, 2, year=2024, week=5, txn_type='waiver')
        make_transaction(db, 3, year=2024, week=6)
        db.session.commit()

        # get_current_year is used inside Transactions.get_by_week; patch it there
        with patch('app.models.transactions.get_current_year', return_value=2024):
            r = client.get('/v1/transactions/week/5')

        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 2
        assert all(t['week'] == 5 for t in data['transactions'])

    def test_week_with_no_transactions_returns_empty(self, client, db):
        make_transaction(db, 1, year=2024, week=3)
        db.session.commit()

        with patch('app.models.transactions.get_current_year', return_value=2024):
            r = client.get('/v1/transactions/week/99')

        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    def test_week_filters_by_current_year_only(self, client, db):
        """Same week from a prior year should NOT appear."""
        make_transaction(db, 1, year=2023, week=5)
        make_transaction(db, 2, year=2024, week=5)
        db.session.commit()

        with patch('app.models.transactions.get_current_year', return_value=2024):
            r = client.get('/v1/transactions/week/5')

        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['year'] == 2024

    def test_week_excludes_incomplete_transactions(self, client, db):
        make_transaction(db, 1, year=2024, week=5, status='pending')
        db.session.commit()

        with patch('app.models.transactions.get_current_year', return_value=2024):
            r = client.get('/v1/transactions/week/5')

        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/team/<id>  (all transactions for a team)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTeamTransactions:

    def test_valid_team_returns_all_types(self, client, db):
        make_team(db, 1, 1, 'Team A')
        make_transaction(db, 1, txn_type='trade')
        make_transaction(db, 2, txn_type='waiver')
        make_roster(db, 1, 1)
        make_roster(db, 2, 1)
        db.session.commit()
        r = client.get('/v1/transactions/team/1')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        assert len(data['transactions']) == 2

    def test_nonexistent_team_returns_404(self, client, db):
        r = client.get('/v1/transactions/team/999')
        data = r.get_json()
        assert r.status_code == 404
        assert data['success'] is False

    def test_team_with_no_transactions_returns_empty(self, client, db):
        make_team(db, 1, 1, 'Team A')
        db.session.commit()
        r = client.get('/v1/transactions/team/1')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    def test_only_returns_transactions_for_that_team(self, client, db):
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')
        make_transaction(db, 1)  # only Team A
        make_transaction(db, 2)  # only Team B
        make_roster(db, 1, 1)
        make_roster(db, 2, 2)
        db.session.commit()
        r = client.get('/v1/transactions/team/1')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1

    def test_excludes_incomplete_transactions(self, client, db):
        make_team(db, 1, 1, 'Team A')
        make_transaction(db, 1, status='complete')
        make_transaction(db, 2, status='pending')
        make_roster(db, 1, 1)
        make_roster(db, 2, 1)
        db.session.commit()
        r = client.get('/v1/transactions/team/1')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/team/<id>/trades  (trades only)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTeamTrades:

    def test_returns_only_trades(self, client, db):
        make_team(db, 1, 1, 'Team A')
        make_transaction(db, 1, txn_type='trade')
        make_transaction(db, 2, txn_type='waiver')
        make_transaction(db, 3, txn_type='free_agent')
        make_roster(db, 1, 1)
        make_roster(db, 2, 1)
        make_roster(db, 3, 1)
        db.session.commit()
        r = client.get('/v1/transactions/team/1/trades')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['type'] == 'trade'

    def test_team_with_only_waivers_returns_empty(self, client, db):
        make_team(db, 1, 1, 'Team A')
        make_transaction(db, 1, txn_type='waiver')
        make_roster(db, 1, 1)
        db.session.commit()
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

    def test_returns_up_to_5_trades(self, client, db):
        for i in range(1, 11):
            make_transaction(db, i, txn_type='trade')
        db.session.commit()
        r = client.get('/v1/transactions/trades/random')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        assert len(data['transactions']) == 5

    def test_returns_all_when_fewer_than_5(self, client, db):
        make_transaction(db, 1, txn_type='trade')
        make_transaction(db, 2, txn_type='trade')
        db.session.commit()
        r = client.get('/v1/transactions/trades/random')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 2

    def test_no_trades_returns_empty(self, client, db):
        make_transaction(db, 1, txn_type='waiver')
        db.session.commit()
        r = client.get('/v1/transactions/trades/random')
        data = r.get_json()
        assert r.status_code == 200
        assert data['transactions'] == []

    def test_excludes_pending_trades(self, client, db):
        make_transaction(db, 1, txn_type='trade', status='pending')
        make_transaction(db, 2, txn_type='trade', status='complete')
        db.session.commit()
        r = client.get('/v1/transactions/trades/random')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['status'] == 'complete'

    def test_excludes_non_trades(self, client, db):
        for i in range(1, 6):
            make_transaction(db, i, txn_type='waiver')
        make_transaction(db, 10, txn_type='trade')
        db.session.commit()
        r = client.get('/v1/transactions/trades/random')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['type'] == 'trade'


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/transactions/trade-tree/<player_sleeper_id>
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTradeTree:

    def test_player_with_trades_returns_info_and_tree(self, client, db):
        make_player(db, 1, 100, 'Justin', 'Jefferson', 'WR')
        make_transaction(db, 1, txn_type='trade', week=2,
                         created_at=datetime(2024, 9, 10))
        make_player_move(db, 1, 100, 1, 'add')
        db.session.commit()
        r = client.get('/v1/transactions/trade-tree/100')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        assert data['player']['sleeper_id'] == 100
        assert data['player']['first_name'] == 'Justin'
        assert len(data['trade_tree']) == 1

    def test_player_not_in_players_table_returns_none_info(self, client, db):
        """Player has moves but no Players record → player_info should be None."""
        make_transaction(db, 1, txn_type='trade')
        make_player_move(db, 1, 999, 1, 'add')
        db.session.commit()
        r = client.get('/v1/transactions/trade-tree/999')
        data = r.get_json()
        assert r.status_code == 200
        assert data['player'] is None
        assert len(data['trade_tree']) == 1

    def test_player_with_no_moves_returns_empty_tree(self, client, db):
        make_player(db, 1, 100, 'Justin', 'Jefferson', 'WR')
        db.session.commit()
        r = client.get('/v1/transactions/trade-tree/100')
        data = r.get_json()
        assert r.status_code == 200
        assert data['player'] is None
        assert data['trade_tree'] == []

    def test_completely_unknown_player_returns_empty(self, client, db):
        r = client.get('/v1/transactions/trade-tree/77777')
        data = r.get_json()
        assert r.status_code == 200
        assert data['player'] is None
        assert data['trade_tree'] == []

    def test_only_complete_transactions_in_tree(self, client, db):
        """Pending and non-complete transactions must be excluded."""
        make_transaction(db, 1, txn_type='trade', status='complete')
        make_transaction(db, 2, txn_type='trade', status='pending')
        make_player_move(db, 1, 100, 1, 'add')
        make_player_move(db, 2, 100, 2, 'drop')
        db.session.commit()
        r = client.get('/v1/transactions/trade-tree/100')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['trade_tree']) == 1
        assert data['trade_tree'][0]['status'] == 'complete'

    def test_multiple_trades_returned_chronologically(self, client, db):
        make_player(db, 1, 100, 'CeeDee', 'Lamb', 'WR')
        # Intentionally insert later date first
        make_transaction(db, 1, txn_type='trade', created_at=datetime(2024, 10, 5))
        make_transaction(db, 2, txn_type='trade', created_at=datetime(2024, 9, 1))
        make_player_move(db, 1, 100, 1, 'add')
        make_player_move(db, 2, 100, 2, 'drop')
        db.session.commit()
        r = client.get('/v1/transactions/trade-tree/100')
        data = r.get_json()
        assert r.status_code == 200
        tree = data['trade_tree']
        assert len(tree) == 2
        # Earlier date should be first
        dates = [t['created_at'] for t in tree]
        assert dates == sorted(dates)

    def test_player_appears_in_add_and_drop(self, client, db):
        """A player traded twice shows both transactions."""
        make_player(db, 1, 100, 'Tyreek', 'Hill', 'WR')
        make_transaction(db, 1, txn_type='trade', created_at=datetime(2024, 9, 1))
        make_transaction(db, 2, txn_type='trade', created_at=datetime(2024, 10, 1))
        make_player_move(db, 1, 100, 1, 'add')   # Team 1 acquires
        make_player_move(db, 2, 100, 1, 'drop')  # Team 1 trades away
        db.session.commit()
        r = client.get('/v1/transactions/trade-tree/100')
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

    def test_transaction_with_no_moves_returns_empty_teams(self, client, db):
        """Transaction exists but has no player or pick moves → empty teams."""
        make_transaction(db, 1, txn_type='trade')
        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success'] is True
        assert data['origin']['transaction_id'] == 1
        assert data['teams'] == {}
        assert data['pick_metadata'] == {}

    def test_simple_player_trade_populates_both_teams(self, client, db):
        """
        Team A (roster 1) trades Player X (sleeper_id=100) to Team B (roster 2).
        Team B (roster 2) trades Player Y (sleeper_id=200) to Team A (roster 1).
        """
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')
        make_player(db, 1, 100, 'Player', 'X', 'WR')
        make_player(db, 2, 200, 'Player', 'Y', 'RB')

        make_transaction(db, 1, txn_type='trade')
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)

        # Team A drops X → Team B adds X; Team B drops Y → Team A adds Y
        make_player_move(db, 1, 100, 1, 'drop')
        make_player_move(db, 1, 100, 2, 'add')
        make_player_move(db, 1, 200, 2, 'drop')
        make_player_move(db, 1, 200, 1, 'add')

        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()

        assert r.status_code == 200
        teams = data['teams']
        assert '1' in teams and '2' in teams

        # Roster 1 acquired Player Y (200)
        assert any(p['sleeper_id'] == 200 for p in teams['1']['acquired_players'])
        # Roster 2 acquired Player X (100)
        assert any(p['sleeper_id'] == 100 for p in teams['2']['acquired_players'])

    def test_unknown_roster_falls_back_to_placeholder_name(self, client, db):
        """Roster ID with no matching Teams row gets a 'Roster N' placeholder."""
        make_transaction(db, 1, txn_type='trade')
        make_roster(db, 1, 99)   # No team with roster_id=99 in DB
        make_player_move(db, 1, 100, 99, 'add')
        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        teams = data['teams']
        assert '99' in teams
        assert teams['99']['team_name'] == 'Roster 99'
        assert teams['99']['team_id'] is None

    def test_chained_trade_tracked_across_transactions(self, client, db):
        """
        Origin (txn 1):  Roster 1 gets Player X (100); Roster 2 gets Player Y (200).
        Subsequent (txn 2):  Roster 1 trades away Player X, gets Player Z (300).
        Roster 2 not involved in txn 2.

        Expected:
          - teams['1']['acquired_players'] = [Player X]
          - teams['1']['transactions'] = [txn 2]
          - teams['2']['acquired_players'] = [Player Y]
          - teams['2']['transactions'] = []
        """
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')
        make_team(db, 3, 3, 'Team C')
        make_player(db, 1, 100, 'Player', 'X', 'WR')
        make_player(db, 2, 200, 'Player', 'Y', 'RB')
        make_player(db, 3, 300, 'Player', 'Z', 'QB')

        origin = datetime(2024, 9, 1)

        # Origin trade
        make_transaction(db, 1, txn_type='trade', created_at=origin)
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_player_move(db, 1, 100, 2, 'drop')  # Team B gives X
        make_player_move(db, 1, 100, 1, 'add')   # Team A gets X
        make_player_move(db, 1, 200, 1, 'drop')  # Team A gives Y
        make_player_move(db, 1, 200, 2, 'add')   # Team B gets Y

        # Subsequent trade: Team A trades X → Team C
        make_transaction(db, 2, txn_type='trade', created_at=origin + timedelta(days=7))
        make_roster(db, 2, 1)
        make_roster(db, 2, 3)
        make_player_move(db, 2, 100, 1, 'drop')  # Team A gives X
        make_player_move(db, 2, 100, 3, 'add')   # Team C gets X
        make_player_move(db, 2, 300, 3, 'drop')  # Team C gives Z
        make_player_move(db, 2, 300, 1, 'add')   # Team A gets Z

        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()

        assert r.status_code == 200
        teams = data['teams']

        # Team A (roster 1)
        assert '1' in teams
        acquired_ids = [p['sleeper_id'] for p in teams['1']['acquired_players']]
        assert 100 in acquired_ids  # Got Player X from origin
        assert len(teams['1']['transactions']) == 1  # Subsequent trade added
        subsequent = teams['1']['transactions'][0]
        assert subsequent['transaction_id'] == 2

        # Team B (roster 2) – not involved in txn 2
        assert '2' in teams
        acquired_ids_b = [p['sleeper_id'] for p in teams['2']['acquired_players']]
        assert 200 in acquired_ids_b
        assert teams['2']['transactions'] == []

        # Team C (roster 3) – NOT in origin branches, should not appear in teams
        assert '3' not in teams

    def test_future_transaction_not_involving_tracked_asset_is_ignored(self, client, db):
        """
        Team A gets Player X in origin trade.
        Team A later acquires Player Z in a waiver that does NOT involve Player X.
        The waiver should NOT appear in Team A's transactions.
        """
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')
        make_player(db, 1, 100, 'Player', 'X', 'WR')
        make_player(db, 3, 300, 'Player', 'Z', 'TE')

        origin = datetime(2024, 9, 1)

        make_transaction(db, 1, txn_type='trade', created_at=origin)
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_player_move(db, 1, 100, 1, 'add')

        # Waiver: Team A adds Player Z (unrelated to Player X)
        make_transaction(db, 2, txn_type='waiver', created_at=origin + timedelta(days=3))
        make_roster(db, 2, 1)
        make_player_move(db, 2, 300, 1, 'add')

        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()

        assert r.status_code == 200
        teams = data['teams']
        assert '1' in teams
        # The waiver did not involve the tracked asset (Player X), so no chain transaction
        assert teams['1']['transactions'] == []

    def test_pick_only_trade_populates_acquired_picks(self, client, db):
        """Trade involving only draft picks (no players)."""
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')

        make_transaction(db, 1, txn_type='trade')
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        # Roster 1 receives a 2025 2nd-round pick originally owned by Roster 2
        make_pick_move(db, 1, season=2025, round_=2, roster_id=2, owner_id=1, previous_owner_id=2)

        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()

        assert r.status_code == 200
        teams = data['teams']
        assert '1' in teams
        picks = teams['1']['acquired_picks']
        assert len(picks) == 1
        assert picks[0]['season'] == 2025
        assert picks[0]['round'] == 2

    def test_pick_with_draft_result_shows_drafted_player(self, client, db):
        """When a traded pick has been used in a draft, the player is surfaced."""
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')
        make_player(db, 5, 500, 'Bryce', 'Young', 'QB')

        make_transaction(db, 1, txn_type='trade')
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_pick_move(db, 1, season=2023, round_=1, roster_id=2, owner_id=1, previous_owner_id=2)

        # The pick was used to draft Bryce Young (sleeper_id=500)
        make_draft_pick(db, season=2023, round_=1, original_roster_id=2,
                        pick_no=1, player_sleeper_id=500, type_='rookie')

        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()

        assert r.status_code == 200
        teams = data['teams']
        picks = teams['1']['acquired_picks']
        assert picks[0]['drafted_player'] is not None
        assert picks[0]['drafted_player']['first_name'] == 'Bryce'
        assert picks[0]['pick_no'] == 1

        # pick_metadata should also contain this pick
        key = '2023:1:2'
        assert key in data['pick_metadata']
        assert data['pick_metadata'][key]['drafted_player']['sleeper_id'] == 500

    def test_pick_drafted_but_player_not_in_players_table(self, client, db):
        """Pick is drafted but the player_sleeper_id has no Players row."""
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')

        make_transaction(db, 1, txn_type='trade')
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_pick_move(db, 1, season=2023, round_=1, roster_id=2, owner_id=1, previous_owner_id=2)
        make_draft_pick(db, season=2023, round_=1, original_roster_id=2,
                        pick_no=3, player_sleeper_id=88888)  # No Players row for 88888

        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()

        assert r.status_code == 200
        teams = data['teams']
        picks = teams['1']['acquired_picks']
        # Pick is present but drafted_player is None
        assert picks[0]['pick_no'] == 3
        assert picks[0]['drafted_player'] is None

    def test_pick_not_yet_drafted_shows_none_player(self, client, db):
        """Future pick with no DraftPicks record → drafted_player=None, pick_no=None."""
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')

        make_transaction(db, 1, txn_type='trade')
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_pick_move(db, 1, season=2026, round_=3, roster_id=2, owner_id=1, previous_owner_id=2)

        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()

        assert r.status_code == 200
        teams = data['teams']
        picks = teams['1']['acquired_picks']
        assert len(picks) == 1
        assert picks[0]['pick_no'] is None
        assert picks[0]['drafted_player'] is None

    def test_waiver_drop_of_acquired_player_tracked_in_chain(self, client, db):
        """
        Team A gets Player X in a trade.
        Team A later drops Player X via a waiver claim (same transaction that adds Player Z).
        This waiver should appear in Team A's chain (the tracked asset was affected).
        """
        make_team(db, 1, 1, 'Team A')
        make_team(db, 2, 2, 'Team B')
        make_player(db, 1, 100, 'Player', 'X', 'WR')
        make_player(db, 3, 300, 'Player', 'Z', 'TE')

        origin = datetime(2024, 9, 1)

        make_transaction(db, 1, txn_type='trade', created_at=origin)
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_player_move(db, 1, 100, 1, 'add')   # Team A gets X

        # Waiver: Team A adds Z, drops X
        make_transaction(db, 2, txn_type='waiver', created_at=origin + timedelta(days=5))
        make_roster(db, 2, 1)
        make_player_move(db, 2, 300, 1, 'add')   # Team A adds Z
        make_player_move(db, 2, 100, 1, 'drop')  # Team A drops X

        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()

        assert r.status_code == 200
        teams = data['teams']
        assert len(teams['1']['transactions']) == 1
        assert teams['1']['transactions'][0]['transaction_id'] == 2

    def test_origin_with_no_roster_data_returns_empty_teams(self, client, db):
        """
        Transaction exists but has player moves without any TransactionRosters rows.
        The roster loop produces nothing → teams_data remains empty.
        Note: origin still returns because the not-moves guard fires before roster loop.
        """
        make_player(db, 1, 100, 'Player', 'X', 'WR')
        make_transaction(db, 1, txn_type='trade')
        # Intentionally add player moves but NO roster rows
        make_player_move(db, 1, 100, 1, 'add')
        db.session.commit()
        r = client.get('/v1/transactions/1/full_trade_tree')
        data = r.get_json()
        assert r.status_code == 200
        assert data['teams'] == {}
