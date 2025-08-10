from flask import Blueprint, jsonify
from app.models.matchups import Matchups

matchups = Blueprint('matchups', __name__)

@matchups.route('/matchups/<int:week_number>', methods=['GET', 'OPTIONS'])
def get_matchups(week_number):

    all_matchups = Matchups.query.filter_by(week=week_number).all()
    
    # Use dict to automatically deduplicate by sleeper_matchup_id (keeps first occurrence)
    unique_matchups_dict = {matchup.sleeper_matchup_id: matchup for matchup in all_matchups}
    unique_matchups = list(unique_matchups_dict.values())
    
    return jsonify(success=True, matchups=[ matchup.serialize() for matchup in unique_matchups ])