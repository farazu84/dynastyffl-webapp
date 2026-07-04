import logging
from flask import Blueprint, jsonify
from app.logic.superlatives import (
    get_player_superlatives,
    get_team_superlatives,
    get_draft_superlatives,
    get_scoring_superlatives,
    get_starter_superlatives,
    get_rivalry_superlatives,
    get_playoff_superlatives,
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


@superlatives.route('/superlatives/scoring', methods=['GET', 'OPTIONS'])
def scoring_superlatives():
    """Scoring superlatives: nuke, robbed, the_franchise"""
    try:
        return jsonify(success=True, superlatives=get_scoring_superlatives())
    except Exception as e:
        logger.exception('Error computing scoring superlatives')
        return jsonify(success=False, error=str(e)), 500


@superlatives.route('/superlatives/starters', methods=['GET', 'OPTIONS'])
def starter_superlatives():
    """Starter superlatives: workhorse, tenured, the_anchor, bench_warmers_revenge"""
    try:
        return jsonify(success=True, superlatives=get_starter_superlatives())
    except Exception as e:
        logger.exception('Error computing starter superlatives')
        return jsonify(success=False, error=str(e)), 500


@superlatives.route('/superlatives/rivalries', methods=['GET', 'OPTIONS'])
def rivalry_superlatives():
    """Rivalry superlatives: bad_blood, kryptonite, free_square"""
    try:
        return jsonify(success=True, superlatives=get_rivalry_superlatives())
    except Exception as e:
        logger.exception('Error computing rivalry superlatives')
        return jsonify(success=False, error=str(e)), 500


@superlatives.route('/superlatives/playoffs', methods=['GET', 'OPTIONS'])
def playoff_superlatives():
    """Playoff superlatives: frequent_flyer, mr_january"""
    try:
        return jsonify(success=True, superlatives=get_playoff_superlatives())
    except Exception as e:
        logger.exception('Error computing playoff superlatives')
        return jsonify(success=False, error=str(e)), 500
