from flask import Blueprint, jsonify, request
from app.logic.league import synchronize_teams, set_league_state, synchronize_matchups, synchronize_players

league = Blueprint('league', __name__)

@league.route('/league/synchronize_teams', methods=['PUT', 'OPTIONS'])
def synchronize_teams_endpoint():
    '''
    Synchronizes the teams with the sleeper API.
    This will update the players on each team in the database, along with the starter, bench, and taxi postions.
    '''
    synchronize_teams()
    return jsonify(success=True, message='Teams synchronized')

@league.route('/league/update_league_state', methods=['PUT', 'OPTIONS'])
def update_league_state():
    '''
    Sets the league state.
    '''
    print('Updating league state')
    set_league_state()
    
    # Refresh the global league state manager after updating
    from app.league_state_manager import refresh_league_state
    refresh_league_state()
    
    return jsonify(success=True, message='League state set and global cache refreshed')

@league.route('/league/refresh_state', methods=['POST', 'OPTIONS'])
def refresh_league_state_endpoint():
    '''
    Manually refresh the global league state cache.
    '''
    try:
        from app.league_state_manager import refresh_league_state, get_current_year, get_current_week
        refresh_league_state()
        
        return jsonify(
            success=True, 
            message='League state cache refreshed',
            current_year=get_current_year(),
            current_week=get_current_week()
        )
    except Exception as e:
        return jsonify(success=False, message=f'Failed to refresh league state: {str(e)}'), 500

@league.route('/league/state', methods=['GET', 'OPTIONS'])
def get_league_state_status():
    '''
    Get current league state information from the global cache.
    '''
    try:
        from app.league_state_manager import get_current_year, get_current_week, league_state_manager
        
        return jsonify(
            success=True,
            current_year=get_current_year(),
            current_week=get_current_week(),
            last_updated=league_state_manager._last_updated.isoformat() if league_state_manager._last_updated else None,
            cache_duration_minutes=league_state_manager._cache_duration.total_seconds() / 60
        )
    except Exception as e:
        return jsonify(success=False, message=f'Failed to get league state: {str(e)}'), 500

@league.route('/league/synchronize_matchups', methods=['PUT', 'OPTIONS'])
def synchronize_matchups_endpoint():
    '''
    Synchronizes the matchups with the sleeper API for the current week.
    Updates points_for, points_against, and completion status.
    '''
    try:
        result = synchronize_matchups()
        return jsonify(success=True, message='Matchups synchronized', result=result)
    except Exception as e:
        return jsonify(success=False, message=f'Matchups sync failed: {str(e)}'), 500

@league.route('/league/synchronize_players', methods=['PUT', 'OPTIONS'])
def synchronize_players_endpoint():
    '''
    Synchronizes players with the Sleeper API.
    Updates existing players and adds new ones based on sleeper_id.
    Syncs all fields from height onwards.
    '''
    try:
        result = synchronize_players()
        return jsonify(success=True, message='Players synchronized', result=result)
    except Exception as e:
        return jsonify(success=False, message=f'Players sync failed: {str(e)}'), 500