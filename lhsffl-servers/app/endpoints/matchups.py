from flask import Blueprint, jsonify
from app.models.matchups import Matchups
from app.models.articles import Articles
from app.models.league_state import LeagueState
from app import db
from app.league_state_manager import get_current_year, get_current_week

matchups = Blueprint('matchups', __name__)

@matchups.route('/matchups/<int:week_number>', methods=['GET', 'OPTIONS'])
def get_matchups(week_number):

    all_matchups = Matchups.query.filter_by(week=week_number).all()
    
    # Use dict to automatically deduplicate by sleeper_matchup_id (keeps first occurrence)
    unique_matchups_dict = {matchup.sleeper_matchup_id: matchup for matchup in all_matchups}
    unique_matchups = list(unique_matchups_dict.values())
    
    return jsonify(success=True, matchups=[ matchup.serialize() for matchup in unique_matchups ])


@matchups.route('/matchups/current_matchups', methods=['GET', 'OPTIONS'])
def get_current_matchup():
    '''
    Get the current matchups for the league - optimized version.
    '''
    current_year = get_current_year()
    current_week = get_current_week()
    
    # Single optimized query with proper indexing
    current_matchups = Matchups.query \
        .filter_by(week=current_week, year=current_year) \
        .order_by(Matchups.sleeper_matchup_id) \
        .all()

    # Efficient deduplication using dict comprehension
    unique_matchups = list({matchup.sleeper_matchup_id: matchup for matchup in current_matchups}.values())
    
    return jsonify(success=True, matchups=[matchup.serialize() for matchup in unique_matchups])


@matchups.route('/matchups/current_matchups/fast', methods=['GET', 'OPTIONS'])
def get_current_matchups_fast():
    '''
    Ultra-fast current matchups using raw SQL for maximum performance.
    '''
    # Get current year and week from global state manager (no DB query!)
    current_year = get_current_year()
    current_week = get_current_week()
    
    sql = """
    SELECT DISTINCT
        m.matchup_id,
        m.year,
        m.week,
        m.sleeper_matchup_id,
        m.sleeper_roster_id,
        m.opponent_sleeper_roster_id,
        m.points_for,
        m.points_against,
        m.completed,
        t1.team_name as team_name,
        t2.team_name as opponent_team_name
    FROM Matchups m
    LEFT JOIN Teams t1 ON m.sleeper_roster_id = t1.sleeper_roster_id
    LEFT JOIN Teams t2 ON m.opponent_sleeper_roster_id = t2.sleeper_roster_id
    WHERE m.year = :current_year AND m.week = :current_week
    ORDER BY m.sleeper_matchup_id
    """
    
    result = db.session.execute(sql, {'current_year': current_year, 'current_week': current_week})
    matchups_data = []
    seen_matchup_ids = set()
    
    for row in result:
        if row[3] not in seen_matchup_ids:  # sleeper_matchup_id deduplication
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
                'team_name': row[9],
                'opponent_team_name': row[10]
            })
            seen_matchup_ids.add(row[3])
    
    return jsonify(success=True, matchups=matchups_data)


@matchups.route('/matchups/<int:matchup_id>/week/<int:week_number>/generate_pregame_report', methods=['GET', 'OPTIONS'])
def get_matchup_articles(matchup_id, week_number):
    '''
    Generate a pregame report, probably best to do this as a bulk job in the future.
    '''

    matchup = Matchups.query.filter_by(week=week_number, sleeper_matchup_id=matchup_id).first()
    
    if not matchup:
        return jsonify(success=False, error="Matchup not found"), 404

    article = Articles.generate_pregame_report(matchup)
    
    if not article:
        return jsonify(success=False, error="Failed to generate pregame report. Check server logs for details."), 500

    return jsonify(success=True, article=article.serialize())


@matchups.route('/matchups/<int:matchup_id>/week/<int:week_number>/generate_post_game_report', methods=['GET', 'OPTIONS'])
def get_matchup_post_game_report(matchup_id, week_number):
    '''
    Generate a post game report.
    '''
    matchup = Matchups.query.filter_by(week=week_number, sleeper_matchup_id=matchup_id).first()
    article = Articles.generate_post_game_report(matchup)

    if not article:
        return jsonify(success=False, error="Failed to generate post game report. Check server logs for details."), 500

    return jsonify(success=True, article=article.serialize())