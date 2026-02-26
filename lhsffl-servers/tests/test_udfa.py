"""
Acceptance tests for the UDFA blind bidding system.

Scenarios
─────────
  Window
    1.  Public window endpoint reflects open / closed / not-yet-open / processed states

  Player Pool  (GET /v1/udfa/players)
    2.  Only eligible players returned (rookies, not drafted, not rostered)
    3.  Each player carries only the requesting team's own bid — never another team's
    4.  Budget summary is included in the response

  Bidding  (POST /v1/udfa/bids)
    5.  Successful bid placement — pending status, budget committed updated
    6.  Upsert: updating the same player's bid amount
    7.  Budget enforcement: cannot over-commit across multiple bids
    8.  Eligibility enforcement: drafted / rostered / non-rookie players rejected
    9.  Window enforcement: cannot bid when window is closed

  My Bids  (GET /v1/udfa/bids)
    10. Returns budget summary + bids for the requesting team only

  Retraction  (DELETE /v1/udfa/bids/<id>)
    11. Successful retraction frees up committed budget
    12. Ownership and status enforcement

  Access Control
    13. Every endpoint enforces the correct auth / role requirements

  Admin: Window Management  (POST /v1/admin/udfa/window)
    14. Create and update; validates required fields and datetime format

  Admin: All Bids  (GET /v1/admin/udfa/bids)
    15. Admin sees every team's bids enriched with team name, waiver order, player info

  Admin: Budget Seeding  (POST /v1/admin/udfa/budgets)
    16. Carryover math: floor((prev_balance − won_bids) / 10) + 100
    17. Skips teams that already have a budget for the target year

  Settlement  (POST /v1/admin/udfa/process)
    18. Single bidder wins
    19. Highest bidder wins
    20. Tie broken by waiver_order (lower = higher priority)
    21. Winner → 'won', losers → 'lost'; window marked processed
    22. Cannot settle twice
    23. Multiple players settled independently in one pass
"""

from datetime import datetime, timedelta

from flask_jwt_extended import create_access_token

from tests.conftest import (
    create_resource,
    make_league_state,
    make_team,
    make_user,
    with_udfa_scenario,
)

YEAR = 2026


# ── Token helpers ─────────────────────────────────────────────────────────────

def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


def _admin_token(app, user_id):
    with app.app_context():
        return create_access_token(
            identity=str(user_id),
            additional_claims={'admin': True, 'team_owner': False},
        )


def _owner_token(app, user_id):
    with app.app_context():
        return create_access_token(
            identity=str(user_id),
            additional_claims={'admin': False, 'team_owner': True},
        )


def _admin_tok(app):
    from app.models.users import Users
    u = Users.query.filter_by(user_name='admin').first()
    return _admin_token(app, u.user_id)


def _owner_tok(app, n=1):
    from app.models.users import Users
    u = Users.query.filter_by(user_name=f'owner{n}').first()
    return _owner_token(app, u.user_id)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Window endpoint
# ═══════════════════════════════════════════════════════════════════════════

class TestWindow:

    def test_no_window_returns_null(self, client, db):
        make_league_state(db, year=YEAR, week=1)
        db.session.commit()
        res = client.get(f'/v1/udfa/window?year={YEAR}')
        assert res.status_code == 200
        assert res.get_json()['window'] is None

    @with_udfa_scenario()
    def test_open_window_is_open_true(self, client, db):
        assert client.get(f'/v1/udfa/window?year={YEAR}').get_json()['window']['is_open'] is True

    @with_udfa_scenario(window_open=False)
    def test_past_closed_window_is_open_false(self, client, db):
        assert client.get(f'/v1/udfa/window?year={YEAR}').get_json()['window']['is_open'] is False

    @with_udfa_scenario(window_processed=True)
    def test_processed_window_is_open_false(self, client, db):
        assert client.get(f'/v1/udfa/window?year={YEAR}').get_json()['window']['is_open'] is False

    def test_window_not_yet_open_is_open_false(self, client, db):
        from app.models.bidding_window import BiddingWindow
        make_league_state(db, year=YEAR, week=1)
        db.session.add(BiddingWindow(
            year=YEAR,
            opens_at=datetime.utcnow() + timedelta(days=1),
            closes_at=datetime.utcnow() + timedelta(days=8),
        ))
        db.session.commit()
        assert client.get(f'/v1/udfa/window?year={YEAR}').get_json()['window']['is_open'] is False


# ═══════════════════════════════════════════════════════════════════════════
# 2-4. Player pool
# ═══════════════════════════════════════════════════════════════════════════

class TestGetUDFAPlayers:

    @with_udfa_scenario()
    def test_returns_only_eligible_players(self, app, client, db):
        res = client.get(f'/v1/udfa/players?year={YEAR}', headers=_bearer(_owner_tok(app)))
        assert res.status_code == 200
        ids = {p['sleeper_id'] for p in res.get_json()['players']}
        assert ids == {501, 502, 503, 506, 507, 508, 509, 510, 511}

    @with_udfa_scenario()
    def test_excludes_drafted_player(self, app, client, db):
        res = client.get(f'/v1/udfa/players?year={YEAR}', headers=_bearer(_owner_tok(app)))
        assert 500 not in {p['sleeper_id'] for p in res.get_json()['players']}

    @with_udfa_scenario()
    def test_excludes_rostered_player(self, app, client, db):
        res = client.get(f'/v1/udfa/players?year={YEAR}', headers=_bearer(_owner_tok(app)))
        assert 504 not in {p['sleeper_id'] for p in res.get_json()['players']}

    @with_udfa_scenario()
    def test_excludes_veteran_player(self, app, client, db):
        res = client.get(f'/v1/udfa/players?year={YEAR}', headers=_bearer(_owner_tok(app)))
        assert 505 not in {p['sleeper_id'] for p in res.get_json()['players']}

    @with_udfa_scenario()
    def test_my_bid_is_null_when_no_bid_placed(self, app, client, db):
        res = client.get(f'/v1/udfa/players?year={YEAR}', headers=_bearer(_owner_tok(app)))
        for player in res.get_json()['players']:
            assert player['my_bid'] is None

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=25)
    def test_my_bid_contains_own_bid_amount(self, app, client, db):
        res = client.get(f'/v1/udfa/players?year={YEAR}', headers=_bearer(_owner_tok(app)))
        players = {p['sleeper_id']: p for p in res.get_json()['players']}
        assert players[501]['my_bid']['amount'] == 25

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=501, year=YEAR, amount=40)
    def test_my_bid_does_not_expose_other_teams_bids(self, app, client, db):
        # Team 2 bid on 501 — team 1 should see my_bid=None
        res = client.get(f'/v1/udfa/players?year={YEAR}', headers=_bearer(_owner_tok(app, n=1)))
        players = {p['sleeper_id']: p for p in res.get_json()['players']}
        assert players[501]['my_bid'] is None

    @with_udfa_scenario()
    def test_budget_included_in_response(self, app, client, db):
        res = client.get(f'/v1/udfa/players?year={YEAR}', headers=_bearer(_owner_tok(app)))
        budget = res.get_json()['budget']
        assert budget['starting_balance'] == 100
        assert budget['available'] == 100
        assert budget['committed'] == 0

    def test_unauthenticated_returns_401(self, client, db):
        assert client.get('/v1/udfa/players').status_code == 401

    @with_udfa_scenario()
    def test_admin_without_team_owner_flag_returns_403(self, app, client, db):
        res = client.get(f'/v1/udfa/players?year={YEAR}', headers=_bearer(_admin_tok(app)))
        assert res.status_code == 403

    @with_udfa_scenario()
    def test_team_owner_with_no_team_link_returns_403(self, app, client, db):
        from app.models.users import Users
        orphan = Users(user_name='orphan', email='orphan@t.com', google_id='gid-orph',
                       first_name='Orphan', last_name='User', admin=False, team_owner=True)
        db.session.add(orphan)
        db.session.commit()
        res = client.get(f'/v1/udfa/players?year={YEAR}',
                         headers=_bearer(_owner_token(app, orphan.user_id)))
        assert res.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# 5-9. Bidding
# ═══════════════════════════════════════════════════════════════════════════

class TestPlaceBid:

    def _place(self, client, token, player_sleeper_id, amount):
        return client.post('/v1/udfa/bids',
                           json={'player_sleeper_id': player_sleeper_id, 'amount': amount},
                           headers=_bearer(token))

    @with_udfa_scenario()
    def test_successful_bid_returns_200_and_pending_status(self, app, client, db):
        res = self._place(client, _owner_tok(app), 501, 30)
        assert res.status_code == 200
        assert res.get_json()['bid']['status'] == 'pending'
        assert res.get_json()['bid']['amount'] == 30

    @with_udfa_scenario()
    def test_bid_reduces_available_budget(self, app, client, db):
        tok = _owner_tok(app)
        self._place(client, tok, 501, 30)
        budget = client.get(f'/v1/udfa/bids?year={YEAR}', headers=_bearer(tok)).get_json()['budget']
        assert budget['committed'] == 30
        assert budget['available'] == 70

    @with_udfa_scenario()
    def test_upsert_updates_existing_bid_amount(self, app, client, db):
        tok = _owner_tok(app)
        self._place(client, tok, 501, 20)
        res = self._place(client, tok, 501, 45)
        assert res.status_code == 200
        assert res.get_json()['bid']['amount'] == 45

    @with_udfa_scenario()
    def test_upsert_only_one_bid_row_per_player(self, app, client, db):
        from app.models.udfa_bids import UDFABids
        tok = _owner_tok(app)
        self._place(client, tok, 501, 20)
        self._place(client, tok, 501, 35)
        assert UDFABids.query.filter_by(team_id=1, player_sleeper_id=501).count() == 1

    @with_udfa_scenario()
    def test_cannot_bid_more_than_available_balance(self, app, client, db):
        assert self._place(client, _owner_tok(app), 501, 101).status_code == 400

    @with_udfa_scenario()
    def test_multiple_bids_cannot_exceed_total_balance(self, app, client, db):
        tok = _owner_tok(app)
        self._place(client, tok, 501, 60)
        assert self._place(client, tok, 502, 50).status_code == 400

    @with_udfa_scenario()
    def test_updating_bid_recalculates_available_correctly(self, app, client, db):
        tok = _owner_tok(app)
        self._place(client, tok, 501, 60)
        self._place(client, tok, 501, 80)  # upsert: now $80 committed
        assert self._place(client, tok, 502, 20).status_code == 200  # 80+20=100, exactly on budget

    @with_udfa_scenario()
    def test_zero_amount_rejected(self, app, client, db):
        assert self._place(client, _owner_tok(app), 501, 0).status_code == 400

    @with_udfa_scenario()
    def test_negative_amount_rejected(self, app, client, db):
        assert self._place(client, _owner_tok(app), 501, -5).status_code == 400

    @with_udfa_scenario()
    def test_non_integer_amount_rejected(self, app, client, db):
        assert self._place(client, _owner_tok(app), 501, 9.99).status_code == 400

    @with_udfa_scenario()
    def test_missing_player_sleeper_id_rejected(self, app, client, db):
        res = client.post('/v1/udfa/bids', json={'amount': 10}, headers=_bearer(_owner_tok(app)))
        assert res.status_code == 400

    @with_udfa_scenario()
    def test_drafted_player_rejected(self, app, client, db):
        assert self._place(client, _owner_tok(app), 500, 10).status_code == 400

    @with_udfa_scenario()
    def test_rostered_player_rejected(self, app, client, db):
        assert self._place(client, _owner_tok(app), 504, 10).status_code == 400

    @with_udfa_scenario()
    def test_veteran_player_rejected(self, app, client, db):
        assert self._place(client, _owner_tok(app), 505, 10).status_code == 400

    @with_udfa_scenario(window_open=False)
    def test_closed_window_rejects_bid(self, app, client, db):
        assert self._place(client, _owner_tok(app), 501, 10).status_code == 400

    def test_unauthenticated_returns_401(self, client, db):
        assert client.post('/v1/udfa/bids', json={}).status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 10. My bids
# ═══════════════════════════════════════════════════════════════════════════

class TestGetMyBids:

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=20)
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=502, year=YEAR, amount=30)
    def test_returns_bids_for_own_team_only(self, app, client, db):
        res = client.get(f'/v1/udfa/bids?year={YEAR}', headers=_bearer(_owner_tok(app)))
        data = res.get_json()
        assert data['success'] is True
        assert len(data['bids']) == 1
        assert data['bids'][0]['player_sleeper_id'] == 501

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=35)
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=502, year=YEAR, amount=25)
    def test_budget_committed_reflects_pending_bids(self, app, client, db):
        budget = client.get(f'/v1/udfa/bids?year={YEAR}',
                            headers=_bearer(_owner_tok(app))).get_json()['budget']
        assert budget['committed'] == 60
        assert budget['available'] == 40

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=50, status='won')
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=502, year=YEAR, amount=10)
    def test_won_bid_counted_in_spent_not_committed(self, app, client, db):
        budget = client.get(f'/v1/udfa/bids?year={YEAR}',
                            headers=_bearer(_owner_tok(app))).get_json()['budget']
        assert budget['spent'] == 50
        assert budget['committed'] == 10
        assert budget['available'] == 90  # 100 - 10 pending (won bids don't block future bids)

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=15)
    def test_bids_include_player_info(self, app, client, db):
        bid = client.get(f'/v1/udfa/bids?year={YEAR}',
                         headers=_bearer(_owner_tok(app))).get_json()['bids'][0]
        assert bid['player']['first_name'] == 'Jerry'  # Jerry Rice, sleeper_id=501

    def test_unauthenticated_returns_401(self, client, db):
        assert client.get('/v1/udfa/bids').status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 11-12. Retraction
# ═══════════════════════════════════════════════════════════════════════════

class TestRetractBid:

    @with_udfa_scenario()
    def test_retract_pending_bid_succeeds(self, app, client, db):
        tok = _owner_tok(app)
        bid_id = client.post('/v1/udfa/bids',
                             json={'player_sleeper_id': 501, 'amount': 40},
                             headers=_bearer(tok)).get_json()['bid']['bid_id']
        res = client.delete(f'/v1/udfa/bids/{bid_id}', headers=_bearer(tok))
        assert res.status_code == 200
        assert res.get_json()['success'] is True

    @with_udfa_scenario()
    def test_retract_frees_budget(self, app, client, db):
        tok = _owner_tok(app)
        bid_id = client.post('/v1/udfa/bids',
                             json={'player_sleeper_id': 501, 'amount': 40},
                             headers=_bearer(tok)).get_json()['bid']['bid_id']
        client.delete(f'/v1/udfa/bids/{bid_id}', headers=_bearer(tok))
        budget = client.get(f'/v1/udfa/bids?year={YEAR}',
                            headers=_bearer(tok)).get_json()['budget']
        assert budget['available'] == 100

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=501, year=YEAR, amount=30)
    def test_cannot_retract_another_teams_bid(self, app, client, db):
        from app.models.udfa_bids import UDFABids
        bid_id = UDFABids.query.first().bid_id
        res = client.delete(f'/v1/udfa/bids/{bid_id}', headers=_bearer(_owner_tok(app, n=1)))
        assert res.status_code == 403

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=40, status='won')
    def test_cannot_retract_won_bid(self, app, client, db):
        from app.models.udfa_bids import UDFABids
        bid_id = UDFABids.query.first().bid_id
        res = client.delete(f'/v1/udfa/bids/{bid_id}', headers=_bearer(_owner_tok(app)))
        assert res.status_code == 400

    @with_udfa_scenario(window_open=False)
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=20)
    def test_cannot_retract_when_window_closed(self, app, client, db):
        from app.models.udfa_bids import UDFABids
        bid_id = UDFABids.query.first().bid_id
        res = client.delete(f'/v1/udfa/bids/{bid_id}', headers=_bearer(_owner_tok(app)))
        assert res.status_code == 400

    @with_udfa_scenario()
    def test_retract_nonexistent_bid_returns_404(self, app, client, db):
        res = client.delete('/v1/udfa/bids/99999', headers=_bearer(_owner_tok(app)))
        assert res.status_code == 404

    def test_unauthenticated_returns_401(self, client, db):
        assert client.delete('/v1/udfa/bids/1').status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 13. Access control
# ═══════════════════════════════════════════════════════════════════════════

class TestAccessControl:

    @with_udfa_scenario()
    def test_players_requires_team_owner(self, app, client, db):
        assert client.get(f'/v1/udfa/players?year={YEAR}',
                          headers=_bearer(_admin_tok(app))).status_code == 403

    @with_udfa_scenario()
    def test_place_bid_requires_team_owner(self, app, client, db):
        res = client.post('/v1/udfa/bids',
                          json={'player_sleeper_id': 501, 'amount': 10},
                          headers=_bearer(_admin_tok(app)))
        assert res.status_code == 403

    def test_my_bids_requires_auth(self, client, db):
        assert client.get('/v1/udfa/bids').status_code == 401

    @with_udfa_scenario()
    def test_admin_bids_rejects_team_owner(self, app, client, db):
        assert client.get(f'/v1/admin/udfa/bids?year={YEAR}',
                          headers=_bearer(_owner_tok(app))).status_code == 403

    @with_udfa_scenario()
    def test_admin_window_rejects_team_owner(self, app, client, db):
        res = client.post('/v1/admin/udfa/window',
                          json={'year': YEAR, 'opens_at': '2026-05-01T00:00:00',
                                'closes_at': '2026-05-15T00:00:00'},
                          headers=_bearer(_owner_tok(app)))
        assert res.status_code == 403

    @with_udfa_scenario()
    def test_admin_budgets_rejects_team_owner(self, app, client, db):
        assert client.post('/v1/admin/udfa/budgets',
                           json={'year': 2027, 'waiver_orders': {}},
                           headers=_bearer(_owner_tok(app))).status_code == 403

    @with_udfa_scenario()
    def test_admin_process_rejects_team_owner(self, app, client, db):
        assert client.post('/v1/admin/udfa/process',
                           json={'year': YEAR},
                           headers=_bearer(_owner_tok(app))).status_code == 403

    def test_admin_bids_requires_auth(self, client, db):
        assert client.get('/v1/admin/udfa/bids').status_code == 401

    def test_admin_window_requires_auth(self, client, db):
        assert client.post('/v1/admin/udfa/window', json={}).status_code == 401

    def test_admin_budgets_requires_auth(self, client, db):
        assert client.post('/v1/admin/udfa/budgets', json={}).status_code == 401

    def test_admin_process_requires_auth(self, client, db):
        assert client.post('/v1/admin/udfa/process', json={}).status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 14. Admin: window management
# ═══════════════════════════════════════════════════════════════════════════

class TestAdminSetWindow:

    @with_udfa_scenario()
    def test_creates_new_window(self, app, client, db):
        res = client.post('/v1/admin/udfa/window', json={
            'year': 2027,
            'opens_at': '2027-04-01T00:00:00',
            'closes_at': '2027-04-15T00:00:00',
        }, headers=_bearer(_admin_tok(app)))
        assert res.status_code == 200
        w = res.get_json()['window']
        assert w['year'] == 2027
        assert w['processed'] is False

    @with_udfa_scenario()
    def test_updates_existing_window_dates(self, app, client, db):
        tok = _admin_tok(app)
        client.post('/v1/admin/udfa/window',
                    json={'year': YEAR, 'opens_at': '2026-05-01T00:00:00',
                          'closes_at': '2026-05-20T00:00:00'},
                    headers=_bearer(tok))
        res = client.post('/v1/admin/udfa/window',
                          json={'year': YEAR, 'opens_at': '2026-06-01T00:00:00',
                                'closes_at': '2026-06-30T00:00:00'},
                          headers=_bearer(tok))
        assert res.status_code == 200
        assert '2026-06' in res.get_json()['window']['closes_at']

    @with_udfa_scenario()
    def test_missing_year_returns_400(self, app, client, db):
        res = client.post('/v1/admin/udfa/window',
                          json={'opens_at': '2026-05-01T00:00:00',
                                'closes_at': '2026-05-15T00:00:00'},
                          headers=_bearer(_admin_tok(app)))
        assert res.status_code == 400

    @with_udfa_scenario()
    def test_invalid_datetime_format_returns_400(self, app, client, db):
        res = client.post('/v1/admin/udfa/window',
                          json={'year': YEAR, 'opens_at': 'not-a-date', 'closes_at': 'also-bad'},
                          headers=_bearer(_admin_tok(app)))
        assert res.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════
# 15. Admin: all bids view
# ═══════════════════════════════════════════════════════════════════════════

class TestAdminGetAllBids:

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=10)
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=502, year=YEAR, amount=11)
    @create_resource('UDFABids', bid_budget_id=3, team_id=3, player_sleeper_id=503, year=YEAR, amount=12)
    def test_admin_sees_all_teams_bids(self, app, client, db):
        res = client.get(f'/v1/admin/udfa/bids?year={YEAR}', headers=_bearer(_admin_tok(app)))
        assert res.status_code == 200
        assert len(res.get_json()['bids']) == 3

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=20)
    def test_bids_include_team_name_and_waiver_order(self, app, client, db):
        bid = client.get(f'/v1/admin/udfa/bids?year={YEAR}',
                         headers=_bearer(_admin_tok(app))).get_json()['bids'][0]
        assert bid['team_name'] == 'Team 1'
        assert bid['waiver_order'] == 1

    @with_udfa_scenario()
    def test_response_includes_budgets_for_all_teams(self, app, client, db):
        budgets = client.get(f'/v1/admin/udfa/bids?year={YEAR}',
                             headers=_bearer(_admin_tok(app))).get_json()['budgets']
        assert len(budgets) == 3

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=15)
    def test_bids_include_player_info(self, app, client, db):
        bid = client.get(f'/v1/admin/udfa/bids?year={YEAR}',
                         headers=_bearer(_admin_tok(app))).get_json()['bids'][0]
        assert bid['player']['sleeper_id'] == 501


# ═══════════════════════════════════════════════════════════════════════════
# 16-17. Admin: budget seeding
# ═══════════════════════════════════════════════════════════════════════════

class TestAdminSeedBudgets:

    @with_udfa_scenario()
    def test_creates_budgets_for_new_year(self, app, client, db):
        res = client.post('/v1/admin/udfa/budgets',
                          json={'year': 2027, 'waiver_orders': {'1': 3, '2': 1, '3': 2}},
                          headers=_bearer(_admin_tok(app)))
        assert res.status_code == 200
        assert len(res.get_json()['budgets']) == 3

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=65, status='won')
    def test_carryover_math_floor_10_percent_of_remaining(self, app, client, db):
        """Team 1: $100 - $65 won = $35 remaining → floor(35 / 10) = 3 → 2027 balance = $103."""
        from app.models.bid_budget import BidBudget
        client.post('/v1/admin/udfa/budgets',
                    json={'year': 2027, 'waiver_orders': {'1': 1, '2': 2, '3': 3}},
                    headers=_bearer(_admin_tok(app)))
        assert BidBudget.query.filter_by(team_id=1, year=2027).first().starting_balance == 103

    def test_no_previous_year_defaults_to_100(self, app, client, db):
        """No prior-year budget data → carryover = 0 → starting balance = $100."""
        make_league_state(db, year=YEAR, week=1)
        admin = make_user(db, user_name='admin', email='admin@t.com',
                          google_id='gid-adm', admin=True)
        for i in range(1, 4):
            make_team(db, team_id=i, sleeper_roster_id=i, team_name=f'Team {i}')
        db.session.commit()
        res = client.post('/v1/admin/udfa/budgets',
                          json={'year': YEAR, 'waiver_orders': {'1': 1, '2': 2, '3': 3}},
                          headers=_bearer(_admin_token(app, admin.user_id)))
        for b in res.get_json()['budgets']:
            assert b['starting_balance'] == 100

    @with_udfa_scenario()
    def test_skips_teams_that_already_have_budget_for_year(self, app, client, db):
        res = client.post('/v1/admin/udfa/budgets',
                          json={'year': YEAR, 'waiver_orders': {}},
                          headers=_bearer(_admin_tok(app)))
        assert res.get_json()['budgets'] == []

    @with_udfa_scenario()
    def test_missing_year_returns_400(self, app, client, db):
        res = client.post('/v1/admin/udfa/budgets',
                          json={'waiver_orders': {}},
                          headers=_bearer(_admin_tok(app)))
        assert res.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════
# 18-23. Settlement
# ═══════════════════════════════════════════════════════════════════════════

class TestSettlement:

    def _process(self, client, token, year=YEAR):
        return client.post('/v1/admin/udfa/process',
                           json={'year': year}, headers=_bearer(token))

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=20)
    def test_single_bidder_wins(self, app, client, db):
        results = {r['player_sleeper_id']: r
                   for r in self._process(client, _admin_tok(app)).get_json()['results']}
        assert results[501]['winner_team_id'] == 1
        assert results[501]['winning_amount'] == 20

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=30)
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=501, year=YEAR, amount=55)
    @create_resource('UDFABids', bid_budget_id=3, team_id=3, player_sleeper_id=501, year=YEAR, amount=20)
    def test_highest_bidder_wins(self, app, client, db):
        results = {r['player_sleeper_id']: r
                   for r in self._process(client, _admin_tok(app)).get_json()['results']}
        assert results[501]['winner_team_id'] == 2  # team 2 bid $55

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=50)
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=501, year=YEAR, amount=50)
    def test_tie_broken_by_waiver_order_lower_wins(self, app, client, db):
        results = {r['player_sleeper_id']: r
                   for r in self._process(client, _admin_tok(app)).get_json()['results']}
        assert results[501]['winner_team_id'] == 1  # waiver_order=1 beats waiver_order=2

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=30)
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=501, year=YEAR, amount=50)
    def test_higher_bid_beats_better_waiver_order(self, app, client, db):
        """$50 > $30 even though team 1 has the better waiver priority."""
        results = {r['player_sleeper_id']: r
                   for r in self._process(client, _admin_tok(app)).get_json()['results']}
        assert results[501]['winner_team_id'] == 2

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=60)
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=501, year=YEAR, amount=40)
    def test_winning_bid_marked_won(self, app, client, db):
        from app.models.udfa_bids import UDFABids
        self._process(client, _admin_tok(app))
        assert UDFABids.query.filter_by(team_id=1, player_sleeper_id=501).first().status == 'won'

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=60)
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=501, year=YEAR, amount=40)
    def test_losing_bids_marked_lost(self, app, client, db):
        from app.models.udfa_bids import UDFABids
        self._process(client, _admin_tok(app))
        assert UDFABids.query.filter_by(team_id=2, player_sleeper_id=501).first().status == 'lost'

    @with_udfa_scenario()
    def test_window_marked_processed_after_settlement(self, app, client, db):
        from app.models.bidding_window import BiddingWindow
        self._process(client, _admin_tok(app))
        assert BiddingWindow.query.filter_by(year=YEAR).first().processed is True

    @with_udfa_scenario()
    def test_cannot_process_twice(self, app, client, db):
        tok = _admin_tok(app)
        self._process(client, tok)
        res = self._process(client, tok)
        assert res.status_code == 400
        assert res.get_json()['success'] is False

    def test_no_window_returns_400(self, app, client, db):
        make_league_state(db, year=YEAR, week=1)
        admin = make_user(db, user_name='admin', email='admin@t.com',
                          google_id='gid-adm', admin=True)
        db.session.commit()
        res = client.post('/v1/admin/udfa/process',
                          json={'year': YEAR},
                          headers=_bearer(_admin_token(app, admin.user_id)))
        assert res.status_code == 400

    @with_udfa_scenario()
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=501, year=YEAR, amount=60)
    @create_resource('UDFABids', bid_budget_id=1, team_id=1, player_sleeper_id=503, year=YEAR, amount=45)
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=501, year=YEAR, amount=30)
    @create_resource('UDFABids', bid_budget_id=2, team_id=2, player_sleeper_id=502, year=YEAR, amount=80)
    @create_resource('UDFABids', bid_budget_id=3, team_id=3, player_sleeper_id=502, year=YEAR, amount=10)
    def test_multiple_players_settled_independently(self, app, client, db):
        results = {r['player_sleeper_id']: r
                   for r in self._process(client, _admin_tok(app)).get_json()['results']}
        assert results[501]['winner_team_id'] == 1  # $60 > $30
        assert results[502]['winner_team_id'] == 2  # $80 > $10
        assert results[503]['winner_team_id'] == 1  # only bidder

    @with_udfa_scenario()
    def test_no_pending_bids_returns_empty_results(self, app, client, db):
        res = self._process(client, _admin_tok(app))
        assert res.status_code == 200
        assert res.get_json()['results'] == []
