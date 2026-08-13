"""
Global League State Manager

This module provides a singleton that stores the current league state
to avoid repeated database queries across the application.

Deliberately caches plain values (year/week), never the live LeagueState ORM
instance. That instance belongs to whatever request's session happened to
load it; once that session commits (expire_on_commit) or is torn down at
request end, the cached object goes detached, and any later attribute access
tries to refresh from a session that no longer exists, raising
sqlalchemy.orm.exc.DetachedInstanceError ("not bound to a Session"). Since
this cache is read from nearly every endpoint, that failure mode takes down
the whole app until the next refresh. Caching primitives sidesteps the
problem entirely — there's no ORM state left to go stale.
"""

import threading
from datetime import datetime, timedelta
from typing import Optional
from app.models.league_state import LeagueState

DEFAULT_YEAR = 2024
DEFAULT_WEEK = 1


class LeagueStateManager:
    """
    Singleton class to manage global league stat
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LeagueStateManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._year = None
            self._week = None
            self._last_updated = None
            self._cache_duration = timedelta(minutes=5)
            self._data_lock = threading.Lock()
            self._initialized = True

    def initialize(self, app_context):
        """
        Initialize the league state on server startup
        """
        with app_context:
            self._refresh_league_state()
            print(f"League State Manager initialized: Year {self.current_year}, Week {self.current_week}")

    def _refresh_league_state(self):
        """
        Refresh league state from database.

        Reads year/week off the ORM instance while it's still attached to this
        session and stores only those plain values — never the instance itself.
        """
        try:
            from app import db
            current_state = db.session.query(LeagueState).filter_by(current=True).first()

            with self._data_lock:
                if current_state is not None:
                    self._year = current_state.year
                    self._week = current_state.week
                self._last_updated = datetime.now()

        except Exception as e:
            print(f"Error refreshing league state: {e}")

    def _should_refresh(self) -> bool:
        """
        Check if cache should be refreshed
        """
        if self._last_updated is None:
            return True
        return datetime.now() - self._last_updated > self._cache_duration

    def _ensure_fresh(self, force_refresh: bool = False):
        if force_refresh or self._should_refresh():
            self._refresh_league_state()

    @property
    def current_year(self) -> int:
        """
        Get current league year
        """
        self._ensure_fresh()
        with self._data_lock:
            return self._year if self._year is not None else DEFAULT_YEAR

    @property
    def current_week(self) -> int:
        """
        Get current league week
        """
        self._ensure_fresh()
        with self._data_lock:
            return self._week if self._week is not None else DEFAULT_WEEK

    def refresh(self):
        """
        Manually refresh league state
        """
        self._refresh_league_state()
        print(f"League state refreshed: Year {self.current_year}, Week {self.current_week}")


# Global singleton instance
league_state_manager = LeagueStateManager()


def get_current_year() -> int:
    """Convenience function to get current league year"""
    return league_state_manager.current_year


def get_current_week() -> int:
    """Convenience function to get current league week"""
    return league_state_manager.current_week


def refresh_league_state():
    """Convenience function to refresh league state"""
    league_state_manager.refresh()
