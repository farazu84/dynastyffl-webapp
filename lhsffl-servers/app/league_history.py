"""
Single source of truth for the league's Sleeper league IDs by season.

Each season is a separate Sleeper league (chained by previous_league_id).
This map is consumed by the historical backfills and any season-aware sync.
"""

# year -> Sleeper league_id (2019 startup through current)
LEAGUE_HISTORY = {
    2019: '419666295387082752',
    2020: '516385651688570880',
    2021: '650601235019292672',
    2022: '785954136989769728',
    2023: '932976884349030400',
    2024: '1063040492125937664',
    2025: '1195252934627844096',
    2026: '1328498202462126080',
}

# The 2019 startup draft ID — all other drafts are rookie drafts.
STARTUP_DRAFT_ID = 424730242209304576


def league_id_for(year):
    """Return the Sleeper league_id for a season, or None if unknown."""
    return LEAGUE_HISTORY.get(int(year))


def current_league_id():
    """Return the league_id for the most recent season in the history map."""
    latest_year = max(LEAGUE_HISTORY)
    return LEAGUE_HISTORY[latest_year]


def seasons():
    """Return all known seasons, ascending."""
    return sorted(LEAGUE_HISTORY.keys())
