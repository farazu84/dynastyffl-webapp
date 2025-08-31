from flask import Blueprint, jsonify
from app.models.matchups import Matchups
from app.models.articles import Articles
from app.models.league_state import LeagueState

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
    Get the current matchups for the league.
    '''

    current_league_state = LeagueState.query.filter_by(current=True).first()
    current_matchup = Matchups.query.filter_by(week=current_league_state.week, year=current_league_state.year).all()

    unique_matchups_dict = {matchup.sleeper_matchup_id: matchup for matchup in current_matchup}
    unique_current_matchups = list(unique_matchups_dict.values())
    return jsonify(success=True, matchups=[ matchup.serialize() for matchup in unique_current_matchups ])


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