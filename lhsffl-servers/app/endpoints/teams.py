from flask import Blueprint, jsonify
from app.models.teams import Teams
from app.models.matchups import Matchups
from app import db

teams = Blueprint('teams', __name__)

@teams.route('/teams', methods=['GET', 'OPTIONS'])
def get_teams():
    from app.models.team_records import TeamRecords
    from app.models.league_state import LeagueState
    
    # Get current year efficiently
    current_league = LeagueState.query.filter_by(current=True).first()
    current_year = current_league.year if current_league else 2024
    
    # Direct join with current year filter and explicit ordering
    teams = Teams.query \
        .join(TeamRecords, Teams.team_id == TeamRecords.team_id) \
        .filter(TeamRecords.year == current_year) \
        .order_by(
            TeamRecords.wins.desc(),
            TeamRecords.points_for.desc()
        ).all()

    return jsonify(success=True, teams=[ team.serialize() for team in teams ])

@teams.route('/teams/<int:team_id>', methods=['GET', 'OPTIONS'])
def get_team(team_id):
    team = Teams.query.get(team_id)
    return jsonify(success=True, team=team.serialize())

@teams.route('/teams/<int:team_id>/matchups', methods=['GET', 'OPTIONS'])
def get_team_matchups(team_id):
    from app.models.team_records import TeamRecords
    from app.models.league_state import LeagueState
    
    # Get team efficiently with error handling
    team = Teams.query.get(team_id)
    if not team:
        return jsonify(success=False, error="Team not found"), 404
    
    # Get current year for filtering (optional optimization)
    current_league = LeagueState.query.filter_by(current=True).first()
    current_year = current_league.year if current_league else 2024
    
    # Optimized query with proper indexing and current year filter
    matchups = Matchups.query \
        .filter_by(sleeper_roster_id=team.sleeper_roster_id, year=current_year) \
        .order_by(Matchups.week) \
        .all()
    
    return jsonify(success=True, matchups=[matchup.serialize() for matchup in matchups])

@teams.route('/teams/<int:team_id>/matchups/fast', methods=['GET', 'OPTIONS'])
def get_team_matchups_fast(team_id):
    """Ultra-fast team matchups using raw SQL for maximum performance"""
    
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
    INNER JOIN LeagueState ls ON m.year = ls.year AND ls.current = 1
    WHERE t1.team_id = :team_id
    ORDER BY m.week
    """
    
    result = db.session.execute(sql, {'team_id': team_id})
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


