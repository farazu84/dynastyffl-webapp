from flask import Blueprint, jsonify
from app.models.teams import Teams

teams = Blueprint('teams', __name__)

@teams.route('/teams', methods=['GET', 'OPTIONS'])
def get_teams():
    teams = Teams.query.all()

    return jsonify(success=True, teams=[ team.serialize() for team in teams ])

@teams.route('/team/<int:team_id>', methods=['GET', 'OPTIONS'])
def get_team(team_id):
    pass


