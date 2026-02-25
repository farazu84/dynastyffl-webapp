"""
Integration tests for admin endpoints.

Scenarios:
  1. Admin can list all team owners
  2. Non-admin and unauthenticated requests to team-owners are rejected
  3. Admin can impersonate a team owner and receives a valid token
  4. Impersonated token carries the correct identity and impersonated_by claim
  5. Impersonating a non-owner or non-existent user is rejected
  6. Non-admin cannot impersonate
"""

from flask_jwt_extended import create_access_token, decode_token

from tests.conftest import create_resource, make_user


# ── helpers ───────────────────────────────────────────────────────────────────

def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


def _admin_token(app, user_id):
    with app.app_context():
        return create_access_token(
            identity=str(user_id),
            additional_claims={'admin': True, 'team_owner': False},
        )


def _user_token(app, user_id):
    with app.app_context():
        return create_access_token(
            identity=str(user_id),
            additional_claims={'admin': False, 'team_owner': True},
        )


# ── Scenario 1: Admin can list team owners ────────────────────────────────────

class TestGetTeamOwners:

    def test_returns_only_team_owners(self, app, client, db):
        admin = make_user(db, user_name='admin', email='admin@example.com',
                          google_id='gid-admin', admin=True, team_owner=False)
        make_user(db, user_name='owner1', email='owner1@example.com',
                  google_id='gid-owner1', first_name='Bo', last_name='Jackson',
                  admin=False, team_owner=True)
        make_user(db, user_name='owner2', email='owner2@example.com',
                  google_id='gid-owner2', first_name='Emmitt', last_name='Smith',
                  admin=False, team_owner=True)
        make_user(db, user_name='nonowner', email='nonowner@example.com',
                  google_id='gid-nonowner', admin=False, team_owner=False)
        db.session.commit()

        token = _admin_token(app, admin.user_id)
        res = client.get('/v1/admin/team-owners', headers=_bearer(token))

        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True
        usernames = {u['user_name'] for u in data['users']}
        assert usernames == {'owner1', 'owner2'}
        assert 'nonowner' not in usernames
        assert 'admin' not in usernames

    def test_response_includes_expected_user_fields(self, app, client, db):
        admin = make_user(db, user_name='admin', email='admin@example.com',
                          google_id='gid-admin', admin=True, team_owner=False)
        make_user(db, user_name='barry', email='barry@example.com',
                  google_id='gid-barry', first_name='Barry', last_name='Sanders',
                  admin=False, team_owner=True)
        db.session.commit()

        token = _admin_token(app, admin.user_id)
        res = client.get('/v1/admin/team-owners', headers=_bearer(token))

        user = res.get_json()['users'][0]
        assert 'user_id' in user
        assert 'user_name' in user
        assert 'first_name' in user
        assert 'last_name' in user
        assert 'password' not in user
        assert 'google_id' not in user

    def test_returns_empty_list_when_no_team_owners(self, app, client, db):
        admin = make_user(db, user_name='admin', email='admin@example.com',
                          google_id='gid-admin', admin=True, team_owner=False)
        db.session.commit()

        token = _admin_token(app, admin.user_id)
        res = client.get('/v1/admin/team-owners', headers=_bearer(token))

        assert res.status_code == 200
        assert res.get_json()['users'] == []


# ── Scenario 2: Access control on team-owners ─────────────────────────────────

class TestGetTeamOwnersAccessControl:

    def test_unauthenticated_request_is_rejected(self, client, db):
        res = client.get('/v1/admin/team-owners')
        assert res.status_code == 401

    def test_non_admin_user_is_forbidden(self, app, client, db):
        owner = make_user(db, user_name='owner', email='owner@example.com',
                          google_id='gid-owner', admin=False, team_owner=True)
        db.session.commit()

        token = _user_token(app, owner.user_id)
        res = client.get('/v1/admin/team-owners', headers=_bearer(token))

        assert res.status_code == 403


# ── Scenario 3: Admin can impersonate a team owner ────────────────────────────

class TestImpersonate:

    def test_admin_receives_valid_token_for_target_user(self, app, client, db):
        admin = make_user(db, user_name='admin', email='admin@example.com',
                          google_id='gid-admin', admin=True, team_owner=False)
        target = make_user(db, user_name='jerryrice', email='jerry.rice@example.com',
                           google_id='gid-jerry', first_name='Jerry', last_name='Rice',
                           admin=False, team_owner=True)
        db.session.commit()

        token = _admin_token(app, admin.user_id)
        res = client.post(f'/v1/admin/impersonate/{target.user_id}', headers=_bearer(token))

        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True
        assert 'access_token' in data
        assert data['user']['user_id'] == target.user_id
        assert data['user']['user_name'] == 'jerryrice'

    def test_impersonated_token_has_target_identity(self, app, client, db):
        admin = make_user(db, user_name='admin', email='admin@example.com',
                          google_id='gid-admin', admin=True, team_owner=False)
        target = make_user(db, user_name='walterpayton', email='walter@example.com',
                           google_id='gid-sweetness', admin=False, team_owner=True)
        db.session.commit()

        admin_token = _admin_token(app, admin.user_id)
        res = client.post(f'/v1/admin/impersonate/{target.user_id}',
                          headers=_bearer(admin_token))
        impersonated_token = res.get_json()['access_token']

        with app.app_context():
            decoded = decode_token(impersonated_token)

        assert decoded['sub'] == str(target.user_id)
        assert decoded['team_owner'] is True
        assert decoded['admin'] is False


# ── Scenario 4: Impersonated token carries impersonated_by claim ──────────────

class TestImpersonatedByClaim:

    def test_token_records_which_admin_initiated_impersonation(self, app, client, db):
        admin = make_user(db, user_name='admin', email='admin@example.com',
                          google_id='gid-admin', admin=True, team_owner=False)
        target = make_user(db, user_name='ronnieLott', email='ronnie@example.com',
                           google_id='gid-ronnie', admin=False, team_owner=True)
        db.session.commit()

        admin_token = _admin_token(app, admin.user_id)
        res = client.post(f'/v1/admin/impersonate/{target.user_id}',
                          headers=_bearer(admin_token))
        impersonated_token = res.get_json()['access_token']

        with app.app_context():
            decoded = decode_token(impersonated_token)

        assert decoded['impersonated_by'] == admin.user_id


# ── Scenario 5: Invalid impersonation targets ─────────────────────────────────

class TestImpersonateInvalidTargets:

    def test_impersonating_nonexistent_user_returns_404(self, app, client, db):
        admin = make_user(db, user_name='admin', email='admin@example.com',
                          google_id='gid-admin', admin=True, team_owner=False)
        db.session.commit()

        token = _admin_token(app, admin.user_id)
        res = client.post('/v1/admin/impersonate/99999', headers=_bearer(token))

        assert res.status_code == 404
        assert res.get_json()['success'] is False

    def test_impersonating_non_owner_user_returns_400(self, app, client, db):
        admin = make_user(db, user_name='admin', email='admin@example.com',
                          google_id='gid-admin', admin=True, team_owner=False)
        non_owner = make_user(db, user_name='spectator', email='spectator@example.com',
                              google_id='gid-spectator', admin=False, team_owner=False)
        db.session.commit()

        token = _admin_token(app, admin.user_id)
        res = client.post(f'/v1/admin/impersonate/{non_owner.user_id}',
                          headers=_bearer(token))

        assert res.status_code == 400
        assert res.get_json()['success'] is False


# ── Scenario 6: Non-admin cannot impersonate ──────────────────────────────────

class TestImpersonateAccessControl:

    def test_unauthenticated_request_is_rejected(self, client, db):
        res = client.post('/v1/admin/impersonate/1')
        assert res.status_code == 401

    def test_non_admin_user_is_forbidden(self, app, client, db):
        owner = make_user(db, user_name='owner', email='owner@example.com',
                          google_id='gid-owner', admin=False, team_owner=True)
        target = make_user(db, user_name='target', email='target@example.com',
                           google_id='gid-target', admin=False, team_owner=True)
        db.session.commit()

        token = _user_token(app, owner.user_id)
        res = client.post(f'/v1/admin/impersonate/{target.user_id}',
                          headers=_bearer(token))

        assert res.status_code == 403
