from flask import Blueprint, jsonify
from app.models.matchups import Matchups
from app.models.articles import Articles

matchups = Blueprint('matchups', __name__)

@matchups.route('/matchups/<int:week_number>', methods=['GET', 'OPTIONS'])
def get_matchups(week_number):

    all_matchups = Matchups.query.filter_by(week=week_number).all()
    
    # Use dict to automatically deduplicate by sleeper_matchup_id (keeps first occurrence)
    unique_matchups_dict = {matchup.sleeper_matchup_id: matchup for matchup in all_matchups}
    unique_matchups = list(unique_matchups_dict.values())
    
    return jsonify(success=True, matchups=[ matchup.serialize() for matchup in unique_matchups ])


@matchups.route('/matchups/<int:matchup_id>/week/<int:week_number>/generate_pregame_report', methods=['GET', 'OPTIONS'])
def get_matchup_articles(matchup_id, week_number):
    '''
    Generate a pregame report, probably best to do this as a bulk job in the future.
    '''

    matchup = Matchups.query.filter_by(week=week_number, sleeper_matchup_id=matchup_id).first()

    article = Articles.generate_pregame_report(matchup)

    return jsonify(success=True, article=article.serialize())