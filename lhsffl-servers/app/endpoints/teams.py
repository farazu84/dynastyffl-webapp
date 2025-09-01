from flask import Blueprint, jsonify
from app.models.teams import Teams
from app.models.matchups import Matchups

teams = Blueprint('teams', __name__)

@teams.route('/teams', methods=['GET', 'OPTIONS'])
def get_teams():
    teams = Teams.query \
        .join(Teams.team_records) \
        .order_by(
            Teams.team_records.property.mapper.class_.wins.desc(),
            Teams.team_records.property.mapper.class_.points_for.desc()
        ).all()

    return jsonify(success=True, teams=[ team.serialize() for team in teams ])

@teams.route('/teams/<int:team_id>', methods=['GET', 'OPTIONS'])
def get_team(team_id):
    team = Teams.query.get(team_id)
    return jsonify(success=True, team=team.serialize())

@teams.route('/teams/<int:team_id>/matchups', methods=['GET', 'OPTIONS'])
def get_team_matchups(team_id):
    team = Teams.query.get(team_id)
    matchups = Matchups.query.filter_by(sleeper_roster_id=team.sleeper_roster_id).order_by(Matchups.week).all()
    return jsonify(success=True, matchups=[ matchup.serialize() for matchup in matchups ])

@teams.route('/teams/<int:team_id>/articles', methods=['GET', 'OPTIONS'])
def get_team_articles(team_id):
    team = Teams.query.get(team_id)
    articles = team.articles
    return jsonify(success=True, articles=[ article.serialize() for article in articles ])


