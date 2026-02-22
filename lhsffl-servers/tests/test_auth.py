"""
Acceptance tests for the auth service.

These tests verify complete user journeys end-to-end rather than individual
endpoint behaviors. Each test represents a real scenario a user would encounter.

Scenarios:
  1. New user signs up via Google and can immediately access the app
  2. Returning user logs back in and their existing account is preserved
  3. Existing email-only account gets linked when user signs in with Google
  4. User can refresh their session and continue using the app
  5. Unauthenticated requests are rejected across all protected routes
  6. Admin and team owner permissions are reflected through the full auth flow
"""

from unittest.mock import patch
from flask_jwt_extended import create_access_token

from tests.conftest import create_resource


# ── helpers ───────────────────────────────────────────────────────────────────

def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


def _google_login(client, google_id='gid-123', email='test@example.com',
                  given_name='Test', family_name='User'):
    payload = {'sub': google_id, 'email': email,
               'given_name': given_name, 'family_name': family_name}
    with patch('app.endpoints.auth.id_token.verify_oauth2_token', return_value=payload):
        return client.post('/v1/auth/google', json={'credential': 'fake-credential'})


# ── Scenario 1: New user signs up via Google ──────────────────────────────────

class TestNewUserSignup:

    def test_new_user_can_sign_up_and_access_their_profile(self, client, db):
        # User authenticates with Google for the first time
        login = _google_login(client, google_id='gid-jerry-rice',
                               email='jerry.rice@example.com',
                               given_name='Jerry', family_name='Rice')
        assert login.status_code == 200
        login_data = login.get_json()
        assert 'access_token' in login_data
        assert 'refresh_token' in login_data

        # User immediately accesses their profile with the returned token
        me = client.get('/v1/auth/me', headers=_bearer(login_data['access_token']))
        assert me.status_code == 200
        profile = me.get_json()['user']
        assert profile['user_id'] == login_data['user']['user_id']
        assert profile['email'] == 'jerry.rice@example.com'
        assert profile['first_name'] == 'Jerry'
        assert profile['last_name'] == 'Rice'

    def test_new_user_profile_does_not_expose_sensitive_fields(self, client, db):
        login = _google_login(client, google_id='gid-willie-mays',
                               email='willie.mays@example.com',
                               given_name='Willie', family_name='Mays')
        token = login.get_json()['access_token']

        me = client.get('/v1/auth/me', headers=_bearer(token))
        profile = me.get_json()['user']
        assert 'password' not in profile
        assert 'google_id' not in profile

    def test_signing_in_twice_does_not_create_duplicate_account(self, client, db):
        from app.models.users import Users
        _google_login(client, google_id='gid-klay', email='klay.thompson@example.com')
        second_login = _google_login(client, google_id='gid-klay',
                                     email='klay.thompson@example.com')

        assert second_login.status_code == 200
        assert Users.query.count() == 1


# ── Scenario 2: Returning user logs back in ───────────────────────────────────

class TestReturningUser:

    @create_resource('Users', user_name='joemontana', email='joe.montana@example.com',
                     google_id='gid-comeback', first_name='Joe', last_name='Montana',
                     admin=False, team_owner=True)
    def test_returning_user_gets_their_existing_account(self, client, db):
        from app.models.users import Users
        original_user = Users.query.filter_by(email='joe.montana@example.com').first()

        login = _google_login(client, google_id='gid-comeback',
                               email='joe.montana@example.com',
                               given_name='Joe', family_name='Montana')
        assert login.status_code == 200

        # Same user_id returned — no new account created
        assert login.get_json()['user']['user_id'] == original_user.user_id
        assert Users.query.count() == 1

    @create_resource('Users', user_name='joemontana', email='joe.montana@example.com',
                     google_id='gid-comeback', first_name='Joe', last_name='Montana',
                     admin=False, team_owner=True)
    def test_returning_user_can_access_profile_after_login(self, client, db):
        login = _google_login(client, google_id='gid-comeback',
                               email='joe.montana@example.com')
        token = login.get_json()['access_token']

        me = client.get('/v1/auth/me', headers=_bearer(token))
        assert me.status_code == 200
        assert me.get_json()['user']['team_owner'] is True


# ── Scenario 3: Existing email account gets linked via Google ─────────────────

class TestEmailAccountLinking:

    @create_resource('Users', user_name='timhardaway', email='tim.hardaway@example.com',
                     first_name='Tim', last_name='Hardaway')
    def test_user_with_email_only_can_sign_in_with_google(self, client, db):
        from app.models.users import Users
        existing = Users.query.filter_by(email='tim.hardaway@example.com').first()

        login = _google_login(client, google_id='gid-ankles',
                               email='tim.hardaway@example.com',
                               given_name='Tim', family_name='Hardaway')
        assert login.status_code == 200

        # Same account returned, not a new one
        assert login.get_json()['user']['user_id'] == existing.user_id
        assert Users.query.count() == 1

    @create_resource('Users', user_name='timhardaway', email='tim.hardaway@example.com',
                     first_name='Tim', last_name='Hardaway')
    def test_linked_account_is_accessible_after_google_login(self, client, db):
        login = _google_login(client, google_id='gid-ankles',
                               email='tim.hardaway@example.com')
        token = login.get_json()['access_token']

        # User can now access their profile via the linked Google account
        me = client.get('/v1/auth/me', headers=_bearer(token))
        assert me.status_code == 200
        assert me.get_json()['user']['email'] == 'tim.hardaway@example.com'


# ── Scenario 4: Token refresh keeps the session alive ────────────────────────

class TestTokenRefreshLifecycle:

    def test_user_can_refresh_session_and_continue_using_app(self, client, db):
        # User logs in and receives both tokens
        login = _google_login(client, google_id='gid-manofsteal',
                               email='rickey.henderson@example.com',
                               given_name='Rickey', family_name='Henderson')
        assert login.status_code == 200
        refresh_token = login.get_json()['refresh_token']
        original_user_id = login.get_json()['user']['user_id']

        # User exchanges their refresh token for a new access token
        refresh = client.post('/v1/auth/refresh', headers=_bearer(refresh_token))
        assert refresh.status_code == 200
        new_access_token = refresh.get_json()['access_token']

        # New access token grants access to the same profile
        me = client.get('/v1/auth/me', headers=_bearer(new_access_token))
        assert me.status_code == 200
        assert me.get_json()['user']['user_id'] == original_user_id

    def test_user_can_logout_successfully(self, client, db):
        login = _google_login(client, google_id='gid-beastmode',
                               email='marshawn.lynch@example.com',
                               given_name='Marshawn', family_name='Lynch')
        token = login.get_json()['access_token']

        logout = client.post('/v1/auth/logout', headers=_bearer(token))
        assert logout.status_code == 200
        assert logout.get_json()['success'] is True


# ── Scenario 5: Unauthenticated requests are rejected ────────────────────────

class TestAuthProtection:

    def test_protected_routes_require_authentication(self, client, db):
        assert client.get('/v1/auth/me').status_code == 401
        assert client.post('/v1/auth/refresh').status_code == 401
        assert client.post('/v1/auth/logout').status_code == 401

    def test_wrong_token_type_is_rejected(self, client, db):
        # Log in to get both token types
        login = _google_login(client, google_id='gid-tooshort',
                               email='too.short@example.com',
                               given_name='Too', family_name='Short')
        tokens = login.get_json()

        # Refresh token cannot be used where access token is expected
        assert client.get('/v1/auth/me',
                          headers=_bearer(tokens['refresh_token'])).status_code == 422
        # Access token cannot be used where refresh token is expected
        assert client.post('/v1/auth/refresh',
                           headers=_bearer(tokens['access_token'])).status_code == 422


# ── Scenario 6: Permissions flow through the full auth cycle ─────────────────

class TestPermissionsFlow:

    @create_resource('Users', user_name='stephcurry', email='steph.curry@example.com',
                     google_id='gid-night-night', first_name='Steph', last_name='Curry',
                     admin=True, team_owner=True)
    def test_admin_user_permissions_visible_after_login(self, client, db):
        login = _google_login(client, google_id='gid-night-night',
                               email='steph.curry@example.com')
        token = login.get_json()['access_token']

        me = client.get('/v1/auth/me', headers=_bearer(token))
        profile = me.get_json()['user']
        assert profile['admin'] is True
        assert profile['team_owner'] is True

    @create_resource('Users', user_name='draymondgreen', email='draymond.green@example.com',
                     google_id='gid-draymond', first_name='Draymond', last_name='Green',
                     admin=True, team_owner=True)
    def test_admin_permissions_carry_through_token_refresh(self, client, db):
        login = _google_login(client, google_id='gid-draymond',
                               email='draymond.green@example.com')
        refresh_token = login.get_json()['refresh_token']

        refresh = client.post('/v1/auth/refresh', headers=_bearer(refresh_token))
        new_token = refresh.get_json()['access_token']

        me = client.get('/v1/auth/me', headers=_bearer(new_token))
        assert me.get_json()['user']['admin'] is True
