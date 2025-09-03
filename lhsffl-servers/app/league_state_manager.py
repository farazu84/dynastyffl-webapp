"""
Global League State Manager

This module provides a singleton that stores the current league state
to avoid repeated database queries across the application.
"""

import threading
from datetime import datetime, timedelta
from typing import Optional
from app.models.league_state import LeagueState


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
            self._current_league_state = None
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
        Refresh league state from database
        """
        try:
            from app import db
            current_state = db.session.query(LeagueState).filter_by(current=True).first()
            
            with self._data_lock:
                self._current_league_state = current_state
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
    
    def get_current_league_state(self, force_refresh: bool = False) -> Optional[LeagueState]:
        """
        Get current league state, refreshing if needed
        """
        if force_refresh or self._should_refresh():
            self._refresh_league_state()
        
        with self._data_lock:
            return self._current_league_state
    
    @property
    def current_year(self) -> int:
        """
        Get current league year
        """
        state = self.get_current_league_state()
        return state.year if state else 2024
    
    @property 
    def current_week(self) -> int:
        """
        Get current league week
        """
        state = self.get_current_league_state()
        return state.week if state else 1
    
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


def get_current_league_state() -> Optional[LeagueState]:
    """Convenience function to get current league state"""
    return league_state_manager.get_current_league_state()


def refresh_league_state():
    """Convenience function to refresh league state"""
    league_state_manager.refresh()
