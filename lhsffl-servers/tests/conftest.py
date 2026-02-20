import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

# Must be set before importing create_app
os.environ.setdefault('LEAGUE_ID', 'test_league_123')


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'


def _use_sqlite(app):
    """Replacement for setup_db that forces SQLite in-memory."""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'


@pytest.fixture(scope='session')
def app():
    with patch('app.setup_db', _use_sqlite), \
         patch('app.setup_scheduler'), \
         patch('app.setup_league_state_manager'):
        from app import create_app
        application = create_app(TestConfig())
    yield application


@pytest.fixture(scope='function')
def db(app):
    from app import db as _db
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    return app.test_client()


# ── Seed helpers ────────────────────────────────────────────────────────────

def make_team(db, team_id, sleeper_roster_id, team_name='Team'):
    from app.models.teams import Teams
    t = Teams(team_id=team_id, sleeper_roster_id=sleeper_roster_id, team_name=team_name)
    db.session.add(t)
    return t


def make_player(db, player_id, sleeper_id, first_name, last_name, position='WR'):
    from app.models.players import Players
    # Explicitly pass booleans - the model defaults ('0') break strict SQLite drivers
    p = Players(
        player_id=player_id,
        sleeper_id=sleeper_id,
        first_name=first_name,
        last_name=last_name,
        position=position,
        taxi=False,
        starter=False,
        active=False,
    )
    db.session.add(p)
    return p


def make_transaction(
    db,
    transaction_id,
    txn_type='trade',
    status='complete',
    year=2024,
    week=3,
    created_at=None,
    sleeper_transaction_id=None,
):
    from app.models.transactions import Transactions
    t = Transactions(
        transaction_id=transaction_id,
        sleeper_transaction_id=sleeper_transaction_id or (1000 + transaction_id),
        year=year,
        week=week,
        type=txn_type,
        status=status,
        sleeper_league_id=999,
        created_at=created_at or datetime(2024, 9, 1) + timedelta(days=transaction_id),
    )
    db.session.add(t)
    return t


def make_roster(db, transaction_id, sleeper_roster_id, is_consenter=True):
    from app.models.transaction_rosters import TransactionRosters
    r = TransactionRosters(
        transaction_id=transaction_id,
        sleeper_roster_id=sleeper_roster_id,
        is_consenter=is_consenter,
    )
    db.session.add(r)
    return r


def make_player_move(db, transaction_id, player_sleeper_id, sleeper_roster_id, action):
    from app.models.transaction_players import TransactionPlayers
    m = TransactionPlayers(
        transaction_id=transaction_id,
        player_sleeper_id=player_sleeper_id,
        sleeper_roster_id=sleeper_roster_id,
        action=action,
    )
    db.session.add(m)
    return m


def make_pick_move(db, transaction_id, season, round_, roster_id, owner_id, previous_owner_id=None):
    from app.models.transaction_draft_picks import TransactionDraftPicks
    p = TransactionDraftPicks(
        transaction_id=transaction_id,
        season=season,
        round=round_,
        roster_id=roster_id,
        owner_id=owner_id,
        previous_owner_id=previous_owner_id,
    )
    db.session.add(p)
    return p


def make_draft_pick(db, season, round_, original_roster_id, pick_no, player_sleeper_id=None, type_='rookie'):
    from app.models.draft_picks import DraftPicks
    dp = DraftPicks(
        season=season,
        round=round_,
        pick_no=pick_no,
        draft_slot=pick_no,
        drafting_roster_id=original_roster_id,
        original_roster_id=original_roster_id,
        player_sleeper_id=player_sleeper_id or 0,
        sleeper_draft_id=9999,
        type=type_,
    )
    db.session.add(dp)
    return dp


def make_league_state(db, year=2024, week=5):
    from app.models.league_state import LeagueState
    ls = LeagueState(league_state_id=1, year=year, week=week, current=True)
    db.session.add(ls)
    return ls
