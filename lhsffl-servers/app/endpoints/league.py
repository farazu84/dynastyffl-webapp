from flask import Blueprint, jsonify, request
from app.logic.league import synchronize_teams

league = Blueprint('league', __name__)

@league.route('/league/synchronize_teams', methods=['PUT', 'OPTIONS'])
def synchronize_teams_endpoint():
    '''
    Synchronizes the teams with the sleeper API.
    This will update the players on each team in the database, along with the starter, bench, and taxi postions.
    '''
    print('Synchronizing teams')
    synchronize_teams()
    return jsonify(success=True, message='Teams synchronized')