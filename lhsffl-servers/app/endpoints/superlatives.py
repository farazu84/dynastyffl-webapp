from flask import Blueprint, jsonify
from app.logic.superlatives import (
    get_player_superlatives,
    get_team_superlatives,
    get_draft_superlatives,
)

superlatives = Blueprint('superlatives', __name__)


@superlatives.route('/superlatives/players', methods=['GET', 'OPTIONS'])
def player_superlatives():
    """Player superlatives: most_traded, most_teams, most_dropped, boomerang"""
    return jsonify(success=True, superlatives=get_player_superlatives())


@superlatives.route('/superlatives/teams', methods=['GET', 'OPTIONS'])
def team_superlatives():
    """Team superlatives: most_trades, frequent_trade_partners, waiver_warriors, draft_capital_movers"""
    return jsonify(success=True, superlatives=get_team_superlatives())


@superlatives.route('/superlatives/draft', methods=['GET', 'OPTIONS'])
def draft_superlatives():
    """Draft superlatives: startup_loyalists, startup_steals, rookie_draft_steals"""
    return jsonify(success=True, superlatives=get_draft_superlatives())
