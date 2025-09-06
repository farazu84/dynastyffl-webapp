from flask import Blueprint, jsonify
from app.models.teams import Teams
from app.models.matchups import Matchups
from app.models.team_records import TeamRecords
from app import db
from app.league_state_manager import get_current_year, get_current_week

teams = Blueprint('teams', __name__)

@teams.route('/teams', methods=['GET', 'OPTIONS'])
def get_teams():
    current_year = get_current_year()
    
    teams = Teams.query \
        .join(TeamRecords, Teams.team_id == TeamRecords.team_id) \
        .filter(TeamRecords.year == current_year) \
        .order_by(
            TeamRecords.wins.desc(),
            TeamRecords.points_for.desc()
        ).all()

    return jsonify(success=True, teams=[ team.serialize_list() for team in teams ])

@teams.route('/teams/<int:team_id>', methods=['GET', 'OPTIONS'])
def get_team(team_id):
    team = Teams.query.get(team_id)
    return jsonify(success=True, team=team.serialize())

@teams.route('/teams/<int:team_id>/matchups', methods=['GET', 'OPTIONS'])
def get_team_matchups(team_id):
    # Get team efficiently with error handling
    team = Teams.query.get(team_id)
    if not team:
        return jsonify(success=False, error="Team not found"), 404
    
    current_year = get_current_year()
    
    matchups = Matchups.query \
        .filter_by(sleeper_roster_id=team.sleeper_roster_id, year=current_year) \
        .order_by(Matchups.week) \
        .all()
    
    return jsonify(success=True, matchups=[matchup.serialize() for matchup in matchups])

@teams.route('/teams/<int:team_id>/matchups/fast', methods=['GET', 'OPTIONS'])
def get_team_matchups_fast(team_id):
    """Ultra-fast team matchups using raw SQL for maximum performance"""
    
    current_year = get_current_year()
    
    sql = """
    SELECT 
        m.matchup_id,
        m.year,
        m.week,
        m.sleeper_matchup_id,
        m.sleeper_roster_id,
        m.opponent_sleeper_roster_id,
        m.points_for,
        m.points_against,
        m.completed,
        t2.team_name as opponent_team_name
    FROM Matchups m
    INNER JOIN Teams t1 ON m.sleeper_roster_id = t1.sleeper_roster_id
    LEFT JOIN Teams t2 ON m.opponent_sleeper_roster_id = t2.sleeper_roster_id
    WHERE t1.team_id = :team_id AND m.year = :current_year
    ORDER BY m.week
    """
    
    result = db.session.execute(sql, {'team_id': team_id, 'current_year': current_year})
    matchups_data = []
    
    for row in result:
        matchups_data.append({
            'matchup_id': row[0],
            'year': row[1],
            'week': row[2], 
            'sleeper_matchup_id': row[3],
            'sleeper_roster_id': row[4],
            'opponent_sleeper_roster_id': row[5],
            'points_for': float(row[6]),
            'points_against': float(row[7]),
            'completed': bool(row[8]),
            'opponent_team_name': row[9]
        })
    
    return jsonify(success=True, matchups=matchups_data)

@teams.route('/teams/<int:team_id>/articles', methods=['GET', 'OPTIONS'])
def get_team_articles(team_id):
    team = Teams.query.get(team_id)
    articles = team.articles
    return jsonify(success=True, articles=[ article.serialize() for article in articles ])


