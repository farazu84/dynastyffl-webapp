from flask import Blueprint, jsonify
from app.models.matchups import Matchups

matchups = Blueprint('matchups', __name__)

@matchups.route('/matchups/<int:week_number>', methods=['GET', 'OPTIONS'])
def get_matchups(week_number):
    matchups = Matchups.query.filter_by(week=week_number).all()
    return jsonify(success=True, matchups=[ matchup.serialize() for matchup in matchups ])