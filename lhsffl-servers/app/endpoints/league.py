from flask import Blueprint, jsonify, request
from app.logic.league import synchronize_teams, set_league_state

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
    return jsonify(success=True, message='League state set')