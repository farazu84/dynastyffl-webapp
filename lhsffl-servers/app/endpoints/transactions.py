from flask import Blueprint, jsonify, request
from app.models.transactions import Transactions
from app.models.teams import Teams
from app.logic.transaction_queries import get_trade_tree, get_full_trade_tree

transactions = Blueprint('transactions', __name__)


@transactions.route('/transactions', methods=['GET', 'OPTIONS'])
def get_transactions():
    """Get transactions with optional filters. Query params: year, week, type, roster_id"""
    txns = Transactions.get_filtered(
        year=request.args.get('year', type=int),
        week=request.args.get('week', type=int),
        txn_type=request.args.get('type'),
        roster_id=request.args.get('roster_id', type=int),
    )
    return jsonify(success=True, transactions=[t.serialize() for t in txns])


@transactions.route('/transactions/<int:transaction_id>', methods=['GET', 'OPTIONS'])
def get_transaction(transaction_id):
    """Get a single transaction by ID."""
    txn = Transactions.query.get(transaction_id)
    if not txn:
        return jsonify(success=False, error='Transaction not found'), 404
    return jsonify(success=True, transaction=txn.serialize())


@transactions.route('/transactions/week/<int:week_number>', methods=['GET', 'OPTIONS'])
def get_transactions_by_week(week_number):
    """Get all transactions for a specific week (current year)."""
    txns = Transactions.get_by_week(week_number)
    return jsonify(success=True, transactions=[t.serialize() for t in txns])


@transactions.route('/transactions/team/<int:team_id>', methods=['GET', 'OPTIONS'])
def get_team_transactions(team_id):
    """Get all transactions for a specific team."""
    team = Teams.query.get(team_id)
    if not team:
        return jsonify(success=False, error='Team not found'), 404
    txns = Transactions.get_for_team(team.sleeper_roster_id)
    return jsonify(success=True, transactions=[t.serialize() for t in txns])


@transactions.route('/transactions/team/<int:team_id>/trades', methods=['GET', 'OPTIONS'])
def get_team_trades(team_id):
    """Get all trades for a specific team."""
    team = Teams.query.get(team_id)
    if not team:
        return jsonify(success=False, error='Team not found'), 404
    txns = Transactions.get_trades_for_team(team.sleeper_roster_id)
    return jsonify(success=True, transactions=[t.serialize() for t in txns])


@transactions.route('/transactions/trades/random', methods=['GET', 'OPTIONS'])
def get_random_trades():
    """Get 5 random trades from the database."""
    txns = Transactions.get_random_trades()
    return jsonify(success=True, transactions=[t.serialize() for t in txns])


@transactions.route('/transactions/trade-tree/<int:player_sleeper_id>', methods=['GET', 'OPTIONS'])
def get_trade_tree_endpoint(player_sleeper_id):
    """Get the trade tree for a player."""
    player_info, txns = get_trade_tree(player_sleeper_id)
    return jsonify(
        success=True,
        player=player_info,
        trade_tree=[t.serialize() for t in txns]
    )


@transactions.route('/transactions/<int:transaction_id>/full_trade_tree', methods=['GET', 'OPTIONS'])
def get_full_trade_tree_endpoint(transaction_id):
    """Get the full trade tree showing the ripple effect for each team involved."""
    origin, teams_data, pick_metadata = get_full_trade_tree(transaction_id)
    if origin is None:
        return jsonify(success=False, error='Transaction not found'), 404
    return jsonify(
        success=True,
        origin=origin.serialize(),
        teams=teams_data,
        pick_metadata=pick_metadata
    )
