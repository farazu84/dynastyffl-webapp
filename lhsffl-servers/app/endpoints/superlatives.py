import logging
from flask import Blueprint, jsonify
from app.logic.superlatives import (
    get_player_superlatives,
    get_team_superlatives,
    get_draft_superlatives,
)

logger = logging.getLogger(__name__)

superlatives = Blueprint('superlatives', __name__)


@superlatives.route('/superlatives/players', methods=['GET', 'OPTIONS'])
def player_superlatives():
    """Player superlatives: most_traded, most_teams, most_dropped, boomerang"""
    try:
        return jsonify(success=True, superlatives=get_player_superlatives())
    except Exception as e:
        logger.exception('Error computing player superlatives')
        return jsonify(success=False, error=str(e)), 500


@superlatives.route('/superlatives/teams', methods=['GET', 'OPTIONS'])
def team_superlatives():
    """Team superlatives: most_trades, frequent_trade_partners, waiver_warriors, draft_capital_movers"""
    try:
        return jsonify(success=True, superlatives=get_team_superlatives())
    except Exception as e:
        logger.exception('Error computing team superlatives')
        return jsonify(success=False, error=str(e)), 500


@superlatives.route('/superlatives/draft', methods=['GET', 'OPTIONS'])
def draft_superlatives():
    """Draft superlatives: startup_loyalists, startup_steals, rookie_draft_steals"""
    try:
        return jsonify(success=True, superlatives=get_draft_superlatives())
    except Exception as e:
        logger.exception('Error computing draft superlatives')
        return jsonify(success=False, error=str(e)), 500
