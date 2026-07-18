"""
Tests for trade-tree production analytics (app.logic.transaction_queries.get_full_trade_tree).

Covers the `production` (per-asset) and `production_totals` (per-side) maps attached to each branch
in teams_data, derived from PlayerWeeklyStats. Starter weeks drive starter_points / games_started /
ppg; total_points includes bench weeks.
"""
from tests.conftest import (
    make_team, make_player, make_transaction, make_roster, make_player_move, make_league_state,
)
from app.logic.transaction_queries import get_full_trade_tree


def seed_stat(db, year, week, roster, player_id, points, is_starter):
    from app.models.player_weekly_stats import PlayerWeeklyStats
    db.session.add(PlayerWeeklyStats(
        year=year, week=week, sleeper_roster_id=roster,
        player_sleeper_id=player_id, points=points, is_starter=is_starter,
    ))


class TestTradeTreeProduction:
    def _seed_two_sided_trade(self, db):
        # Roster 1 acquires players 101 (productive) and 105 (bench-only); roster 2 acquires 102.
        make_team(db, team_id=1, sleeper_roster_id=1, team_name='Side One')
        make_team(db, team_id=2, sleeper_roster_id=2, team_name='Side Two')
        make_player(db, player_id=101, sleeper_id=101, first_name='Star', last_name='WR', position='WR')
        make_player(db, player_id=102, sleeper_id=102, first_name='Solid', last_name='RB', position='RB')
        make_player(db, player_id=105, sleeper_id=105, first_name='Bench', last_name='Guy', position='WR')

        make_transaction(db, transaction_id=1, txn_type='trade')
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_player_move(db, 1, 101, 1, 'add')
        make_player_move(db, 1, 101, 2, 'drop')
        make_player_move(db, 1, 105, 1, 'add')
        make_player_move(db, 1, 102, 2, 'add')
        make_player_move(db, 1, 102, 1, 'drop')

        # 101 for roster 1: 2 starts (20 + 10) + 1 bench (5)  -> sp 30, gs 2, total 35, ppg 15
        seed_stat(db, 2024, 1, 1, 101, 20, True)
        seed_stat(db, 2024, 2, 1, 101, 10, True)
        seed_stat(db, 2024, 3, 1, 101, 5, False)
        # 105 for roster 1: bench only (3)                    -> sp 0, gs 0, total 3
        seed_stat(db, 2024, 1, 1, 105, 3, False)
        # 102 for roster 2: 1 start (8)                       -> sp 8, gs 1, total 8, ppg 8
        seed_stat(db, 2024, 1, 2, 102, 8, True)
        # Contamination guard: 102 (side TWO's asset) also has a big week on roster 1 in some
        # unrelated stint. It must NOT count toward side ONE — 102 is not side one's asset.
        seed_stat(db, 2024, 5, 1, 102, 99, True)
        db.session.commit()

    def test_per_asset_production(self, db):
        self._seed_two_sided_trade(db)
        _origin, teams_data, _pick_meta, _exp = get_full_trade_tree(1)

        prod1 = teams_data[1]['production']
        assert prod1[101] == {'starter_points': 30.0, 'games_started': 2, 'total_points': 35.0, 'ppg': 15.0}
        # Bench-only asset is recorded but has no started games (frontend hides the headline).
        assert prod1[105]['games_started'] == 0
        assert prod1[105]['starter_points'] == 0.0
        assert prod1[105]['total_points'] == 3.0
        # A player who never played for this side has no entry.
        assert 102 not in prod1

        prod2 = teams_data[2]['production']
        assert prod2[102] == {'starter_points': 8.0, 'games_started': 1, 'total_points': 8.0, 'ppg': 8.0}

    def test_per_side_totals(self, db):
        self._seed_two_sided_trade(db)
        _origin, teams_data, _pick_meta, _exp = get_full_trade_tree(1)

        # Side One: 101 (sp30/gs2/tot35) + 105 (sp0/gs0/tot3) — the 99-pt week from 102 on roster 1
        # must NOT leak in (102 belongs to side two).
        assert 102 not in teams_data[1]['production']
        assert teams_data[1]['production_totals'] == {
            'starter_points': 30.0, 'games_started': 2, 'total_points': 38.0, 'ppg': 15.0,
        }
        # Side Two: just 102
        assert teams_data[2]['production_totals'] == {
            'starter_points': 8.0, 'games_started': 1, 'total_points': 8.0, 'ppg': 8.0,
        }

    def test_unplayed_future_weeks_excluded(self, db):
        # Sleeper pre-populates the upcoming season's weeks (set lineup, 0 pts). Those must NOT
        # count as games started. League state = 2026 wk 1, so all of 2026 is unplayed.
        make_league_state(db, year=2026, week=1)
        make_team(db, team_id=1, sleeper_roster_id=1, team_name='Side One')
        make_team(db, team_id=2, sleeper_roster_id=2, team_name='Side Two')
        make_player(db, player_id=101, sleeper_id=101, first_name='Terry', last_name='Mac', position='WR')
        make_transaction(db, transaction_id=1, txn_type='trade')
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_player_move(db, 1, 101, 1, 'add')
        make_player_move(db, 1, 101, 2, 'drop')

        # Played: 2025 weeks 1-3 started (10 each).
        for wk in (1, 2, 3):
            seed_stat(db, 2025, wk, 1, 101, 10, True)
        # Unplayed future season: 2026 weeks 1-18 "started" with 0 pts (must be ignored).
        for wk in range(1, 19):
            seed_stat(db, 2026, wk, 1, 101, 0, True)
        db.session.commit()

        _origin, teams_data, _pick_meta, _exp = get_full_trade_tree(1)
        prod = teams_data[1]['production'][101]
        assert prod['games_started'] == 3   # not 21
        assert prod['starter_points'] == 30.0
        assert prod['ppg'] == 10.0
        assert teams_data[1]['production_totals']['games_started'] == 3

    def test_no_stats_gives_zeroed_totals(self, db):
        # Same trade, but no PlayerWeeklyStats seeded -> empty production, zeroed totals.
        make_team(db, team_id=1, sleeper_roster_id=1, team_name='Side One')
        make_team(db, team_id=2, sleeper_roster_id=2, team_name='Side Two')
        make_player(db, player_id=101, sleeper_id=101, first_name='Star', last_name='WR', position='WR')
        make_transaction(db, transaction_id=1, txn_type='trade')
        make_roster(db, 1, 1)
        make_roster(db, 1, 2)
        make_player_move(db, 1, 101, 1, 'add')
        make_player_move(db, 1, 101, 2, 'drop')
        db.session.commit()

        _origin, teams_data, _pick_meta, _exp = get_full_trade_tree(1)
        assert teams_data[1]['production'] == {}
        assert teams_data[1]['production_totals'] == {
            'starter_points': 0.0, 'games_started': 0, 'total_points': 0.0, 'ppg': 0.0,
        }
