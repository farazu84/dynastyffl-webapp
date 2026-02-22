"""
Test configuration and shared fixtures/factories.

Layers
──────
1. App / DB fixtures        – pytest fixtures for the Flask app and SQLite in-memory DB
2. Low-level helpers        – make_team(), make_player(), …  (fine-grained inserts)
3. create_league()          – one call to seed a full standard league
4. Decorator factories      – @with_trade, @with_waiver, @with_draft_pick
                              wrap a test method, create DB rows via the `db` fixture,
                              and inject the created object as a named kwarg

Decorator usage
───────────────
    class TestSomething:
        @with_trade(roster_ids=[1, 2], adds={1: [101], 2: [102]}, drops={1: [102], 2: [101]})
        def test_foo(self, client, db, league, trade):
            ...

        @with_trade(name='origin',   roster_ids=[1, 2], adds={1: [101]})
        @with_trade(name='followup', roster_ids=[1, 3], adds={3: [101]}, drops={1: [101]})
        def test_chain(self, client, db, league, origin, followup):
            ...
"""

import os
import re
import inspect
import importlib
from itertools import count
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from unittest.mock import patch

import pytest

# Must be set before importing create_app
os.environ.setdefault('LEAGUE_ID', 'test_league_123')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test-google-client-id')

# ── Unique-ID counters (module-level; reset per process, fine for function-scoped DBs) ──
_sleeper_txn_ids = count(start=10_000)


# ═══════════════════════════════════════════════════════════════════════════
# 1. App / DB fixtures
# ═══════════════════════════════════════════════════════════════════════════

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret-key-that-is-long-enough-for-hmac'


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


# ═══════════════════════════════════════════════════════════════════════════
# 2. Low-level row helpers
# ═══════════════════════════════════════════════════════════════════════════

def make_user(db, user_name='testuser', email='test@example.com', google_id='google-sub-123',
              first_name='Test', last_name='User', admin=False, team_owner=False):
    from app.models.users import Users
    u = Users(
        user_name=user_name,
        first_name=first_name,
        last_name=last_name,
        email=email,
        google_id=google_id,
        admin=admin,
        team_owner=team_owner,
    )
    db.session.add(u)
    db.session.flush()  # populate user_id without requiring an explicit commit
    return u


def make_team(db, team_id, sleeper_roster_id, team_name='Team'):
    from app.models.teams import Teams
    t = Teams(team_id=team_id, sleeper_roster_id=sleeper_roster_id, team_name=team_name)
    db.session.add(t)
    return t


def make_player(db, player_id, sleeper_id, first_name, last_name, position='WR'):
    from app.models.players import Players
    # Explicitly pass booleans – the model defaults ('0') break strict SQLite drivers
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
        sleeper_transaction_id=sleeper_transaction_id or next(_sleeper_txn_ids),
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


# ═══════════════════════════════════════════════════════════════════════════
# 3. create_league()  – seed a complete standard league in one call
# ═══════════════════════════════════════════════════════════════════════════

# Positions cycled across the player pool
_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K']


@dataclass
class League:
    """Holds references to every object seeded by create_league()."""
    teams: list
    players: list
    league_state: object

    # ── Convenience look-ups ────────────────────────────────────────────
    def team(self, roster_id: int):
        """Return the Team with the given roster_id."""
        return next(t for t in self.teams if t.sleeper_roster_id == roster_id)

    def player(self, sleeper_id: int):
        """Return the Player with the given sleeper_id."""
        return next(p for p in self.players if p.sleeper_id == sleeper_id)

    @property
    def roster_ids(self) -> list:
        return [t.sleeper_roster_id for t in self.teams]

    @property
    def player_ids(self) -> list:
        return [p.sleeper_id for p in self.players]


def create_league(db, num_teams: int = 4, players_per_team: int = 5, year: int = 2024, week: int = 5) -> League:
    """
    Seed a complete standard league and return a League object.

    Teams:   roster_ids 1 … num_teams
    Players: sleeper_ids 101 … 101 + (num_teams * players_per_team) - 1
             positions cycle through QB/RB/WR/TE/K
    League state: current=True, given year/week
    """
    teams = []
    for i in range(1, num_teams + 1):
        teams.append(make_team(db, team_id=i, sleeper_roster_id=i, team_name=f'Team {i}'))

    players = []
    for i in range(num_teams * players_per_team):
        sleeper_id = 101 + i
        pos = _POSITIONS[i % len(_POSITIONS)]
        players.append(make_player(
            db,
            player_id=sleeper_id,
            sleeper_id=sleeper_id,
            first_name=f'Player',
            last_name=f'{sleeper_id}',
            position=pos,
        ))

    league_state = make_league_state(db, year=year, week=week)
    db.session.commit()

    return League(teams=teams, players=players, league_state=league_state)


@pytest.fixture(scope='function')
def league(db):
    """Pytest fixture: creates a standard 4-team league and commits it."""
    return create_league(db)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Decorator factories
# ═══════════════════════════════════════════════════════════════════════════
#
# Each decorator:
#   • Accepts column-level kwargs that map directly to DB fields
#   • Strips its injected kwarg (e.g. 'trade') from the visible function
#     signature so pytest does NOT attempt to resolve it as a fixture
#   • Commits the new rows, then calls the original test with the object
#     injected as a keyword argument
#
# Stacking works naturally – each decorator peels one param from the sig:
#
#   @with_trade(name='origin',   ...)    ← outermost, pytest sees this sig
#   @with_trade(name='followup', ...)    ← inner
#   def test_foo(self, client, db, league, origin, followup): ...


def _strip_params(fn, *param_names):
    """Return fn's signature with param_names removed (used to hide injected kwargs from pytest)."""
    sig = inspect.signature(fn)
    params = [p for name, p in sig.parameters.items() if name not in param_names]
    return sig.replace(parameters=params)


def with_trade(
    name: str = 'trade',
    *,
    roster_ids: List[int] = (),
    adds: dict = None,
    drops: dict = None,
    picks: List[dict] = (),
    year: int = 2024,
    week: int = 3,
    status: str = 'complete',
    created_at: Optional[datetime] = None,
):
    """
    Decorator: create a trade transaction and inject it into the test.

    Args:
        name        Kwarg name injected into the test (default: 'trade').
        roster_ids  Teams involved → TransactionRosters rows.
        adds        {roster_id: [player_sleeper_id, ...]} → action='add' rows.
        drops       {roster_id: [player_sleeper_id, ...]} → action='drop' rows.
        picks       List of dicts passed directly to TransactionDraftPicks:
                    [{'season': 2025, 'round': 2, 'roster_id': 2,
                      'owner_id': 1, 'previous_owner_id': 2}]
        year, week, status, created_at  Columns on the Transactions row.

    Example:
        @with_trade(roster_ids=[1, 2],
                    adds={1: [101], 2: [102]},
                    drops={1: [102], 2: [101]})
        def test_foo(self, client, db, league, trade): ...
    """
    _adds  = adds  or {}
    _drops = drops or {}

    def decorator(fn):
        new_sig = _strip_params(fn, name)

        def wrapper(*args, **kwargs):
            from app.models.transactions import Transactions
            from app.models.transaction_rosters import TransactionRosters
            from app.models.transaction_players import TransactionPlayers
            from app.models.transaction_draft_picks import TransactionDraftPicks

            db = kwargs['db']
            at = created_at or datetime(2024, 9, 1)

            txn = Transactions(
                sleeper_transaction_id=next(_sleeper_txn_ids),
                year=year, week=week,
                type='trade', status=status,
                sleeper_league_id=999,
                created_at=at,
            )
            db.session.add(txn)
            db.session.flush()  # populate txn.transaction_id

            for rid in roster_ids:
                db.session.add(TransactionRosters(
                    transaction_id=txn.transaction_id,
                    sleeper_roster_id=rid,
                    is_consenter=True,
                ))
            for rid, player_ids in _adds.items():
                for pid in player_ids:
                    db.session.add(TransactionPlayers(
                        transaction_id=txn.transaction_id,
                        player_sleeper_id=pid,
                        sleeper_roster_id=rid,
                        action='add',
                    ))
            for rid, player_ids in _drops.items():
                for pid in player_ids:
                    db.session.add(TransactionPlayers(
                        transaction_id=txn.transaction_id,
                        player_sleeper_id=pid,
                        sleeper_roster_id=rid,
                        action='drop',
                    ))
            for pick in picks:
                db.session.add(TransactionDraftPicks(
                    transaction_id=txn.transaction_id, **pick,
                ))

            db.session.commit()
            kwargs[name] = txn
            return fn(*args, **kwargs)

        wrapper.__name__      = fn.__name__
        wrapper.__qualname__  = fn.__qualname__
        wrapper.__doc__       = fn.__doc__
        wrapper.__signature__ = new_sig
        return wrapper

    return decorator


def with_waiver(
    name: str = 'waiver',
    *,
    roster_id: int,
    add: Optional[int] = None,
    drop: Optional[int] = None,
    year: int = 2024,
    week: int = 3,
    status: str = 'complete',
    created_at: Optional[datetime] = None,
):
    """
    Decorator: create a waiver/free-agent transaction and inject it.

    Args:
        name       Kwarg name injected into the test (default: 'waiver').
        roster_id  The claiming team's roster ID.
        add        player_sleeper_id to add (optional).
        drop       player_sleeper_id to drop to make room (optional).
        year, week, status, created_at  Columns on the Transactions row.

    Example:
        @with_waiver(roster_id=1, add=101, drop=102)
        def test_foo(self, client, db, league, waiver): ...
    """
    def decorator(fn):
        new_sig = _strip_params(fn, name)

        def wrapper(*args, **kwargs):
            from app.models.transactions import Transactions
            from app.models.transaction_rosters import TransactionRosters
            from app.models.transaction_players import TransactionPlayers

            db  = kwargs['db']
            at  = created_at or datetime(2024, 9, 1)

            txn = Transactions(
                sleeper_transaction_id=next(_sleeper_txn_ids),
                year=year, week=week,
                type='waiver', status=status,
                sleeper_league_id=999,
                created_at=at,
            )
            db.session.add(txn)
            db.session.flush()

            db.session.add(TransactionRosters(
                transaction_id=txn.transaction_id,
                sleeper_roster_id=roster_id,
                is_consenter=True,
            ))
            if add is not None:
                db.session.add(TransactionPlayers(
                    transaction_id=txn.transaction_id,
                    player_sleeper_id=add,
                    sleeper_roster_id=roster_id,
                    action='add',
                ))
            if drop is not None:
                db.session.add(TransactionPlayers(
                    transaction_id=txn.transaction_id,
                    player_sleeper_id=drop,
                    sleeper_roster_id=roster_id,
                    action='drop',
                ))

            db.session.commit()
            kwargs[name] = txn
            return fn(*args, **kwargs)

        wrapper.__name__      = fn.__name__
        wrapper.__qualname__  = fn.__qualname__
        wrapper.__doc__       = fn.__doc__
        wrapper.__signature__ = new_sig
        return wrapper

    return decorator


def _camel_to_snake(name):
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def create_resource(model_name, *, commit=True, **fields):
    """
    Decorator: insert a single row into the test DB before the test runs.

    The model is imported lazily to avoid circular imports. The module path is
    derived automatically: 'Users' -> app.models.users, 'DraftPicks' -> app.models.draft_picks.

    Args:
        model_name    Model class name as a string, e.g. 'Users', 'DraftPicks'.
        commit        Commit after adding (default True); pass False to only flush.
        **fields      Column values forwarded directly to the model constructor.

    Example:
        @create_resource('Transactions', type='free_agent', status='complete',
                         sleeper_transaction_id=1, year=2024, week=1, sleeper_league_id=999)
        def test_something(self, client, db):
            ...
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            module = importlib.import_module(f'app.models.{_camel_to_snake(model_name)}')
            model_class = getattr(module, model_name)
            db = kwargs['db']
            db.session.add(model_class(**fields))
            if commit:
                db.session.commit()
            else:
                db.session.flush()
            return fn(*args, **kwargs)

        wrapper.__name__      = fn.__name__
        wrapper.__qualname__  = fn.__qualname__
        wrapper.__doc__       = fn.__doc__
        wrapper.__signature__ = inspect.signature(fn)
        return wrapper

    return decorator


def with_draft_pick(
    name: str = 'draft_pick',
    *,
    season: int,
    round: int,
    original_roster_id: int,
    pick_no: int,
    player_sleeper_id: Optional[int] = None,
    type: str = 'rookie',
):
    """
    Decorator: create a DraftPicks row and inject it.

    Args:
        name               Kwarg name injected into the test (default: 'draft_pick').
        season             Draft year.
        round              Draft round.
        original_roster_id The team that originally owned this pick.
        pick_no            Overall pick number.
        player_sleeper_id  Drafted player's sleeper ID (None if not yet drafted).
        type               'rookie' | 'startup' | 'expansion'.

    Example:
        @with_draft_pick(season=2025, round=1, original_roster_id=2, pick_no=3)
        def test_foo(self, client, db, league, draft_pick): ...
    """
    def decorator(fn):
        new_sig = _strip_params(fn, name)

        def wrapper(*args, **kwargs):
            from app.models.draft_picks import DraftPicks

            db = kwargs['db']
            dp = DraftPicks(
                season=season,
                round=round,
                pick_no=pick_no,
                draft_slot=pick_no,
                drafting_roster_id=original_roster_id,
                original_roster_id=original_roster_id,
                player_sleeper_id=player_sleeper_id or 0,
                sleeper_draft_id=next(_sleeper_txn_ids),
                type=type,
            )
            db.session.add(dp)
            db.session.commit()
            kwargs[name] = dp
            return fn(*args, **kwargs)

        wrapper.__name__      = fn.__name__
        wrapper.__qualname__  = fn.__qualname__
        wrapper.__doc__       = fn.__doc__
        wrapper.__signature__ = new_sig
        return wrapper

    return decorator
