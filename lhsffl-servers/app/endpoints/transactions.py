from flask import Blueprint, jsonify, request
from sqlalchemy.sql.expression import func
from app.models.transactions import Transactions
from app.models.transaction_players import TransactionPlayers
from app.models.transaction_rosters import TransactionRosters
from app.models.teams import Teams
from app.models.players import Players
from app import db
from app.league_state_manager import get_current_year

transactions = Blueprint('transactions', __name__)


@transactions.route('/transactions', methods=['GET', 'OPTIONS'])
def get_transactions():
    """
    Get transactions with optional filters.
    Query params: year, week, type, roster_id
    """
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    txn_type = request.args.get('type')
    roster_id = request.args.get('roster_id', type=int)

    query = Transactions.query

    if year:
        query = query.filter_by(year=year)
    if week:
        query = query.filter_by(week=week)
    if txn_type:
        query = query.filter_by(type=txn_type)
    if roster_id:
        query = query.join(TransactionRosters).filter(
            TransactionRosters.sleeper_roster_id == roster_id
        )

    query = query.filter_by(status='complete')
    query = query.order_by(Transactions.created_at.desc())

    txns = query.all()
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
    current_year = get_current_year()
    txns = Transactions.query \
        .filter_by(week=week_number, year=current_year, status='complete') \
        .order_by(Transactions.created_at.desc()) \
        .all()
    return jsonify(success=True, transactions=[t.serialize() for t in txns])


@transactions.route('/transactions/team/<int:team_id>', methods=['GET', 'OPTIONS'])
def get_team_transactions(team_id):
    """Get all transactions for a specific team."""
    team = Teams.query.get(team_id)
    if not team:
        return jsonify(success=False, error='Team not found'), 404

    txns = Transactions.query \
        .join(TransactionRosters) \
        .filter(TransactionRosters.sleeper_roster_id == team.sleeper_roster_id) \
        .filter(Transactions.status == 'complete') \
        .order_by(Transactions.created_at.desc()) \
        .all()
    return jsonify(success=True, transactions=[t.serialize() for t in txns])


@transactions.route('/transactions/team/<int:team_id>/trades', methods=['GET', 'OPTIONS'])
def get_team_trades(team_id):
    """Get all trades for a specific team."""
    team = Teams.query.get(team_id)
    if not team:
        return jsonify(success=False, error='Team not found'), 404

    txns = Transactions.query \
        .join(TransactionRosters) \
        .filter(TransactionRosters.sleeper_roster_id == team.sleeper_roster_id) \
        .filter(Transactions.type == 'trade') \
        .filter(Transactions.status == 'complete') \
        .order_by(Transactions.created_at.desc()) \
        .all()
    return jsonify(success=True, transactions=[t.serialize() for t in txns])


@transactions.route('/transactions/trades/random', methods=['GET', 'OPTIONS'])
def get_random_trades():
    """Get 5 random trades from the database."""
    txns = Transactions.query \
        .filter_by(type='trade', status='complete') \
        .order_by(func.rand()) \
        .limit(5) \
        .all()
    return jsonify(success=True, transactions=[t.serialize() for t in txns])


@transactions.route('/transactions/trade-tree/<int:player_sleeper_id>', methods=['GET', 'OPTIONS'])
def get_trade_tree(player_sleeper_id):
    """
    Get the trade tree for a player: all transactions where this player was
    added or dropped, ordered chronologically.
    """
    player_moves = TransactionPlayers.query \
        .filter_by(player_sleeper_id=player_sleeper_id) \
        .all()

    if not player_moves:
        return jsonify(success=True, player=None, trade_tree=[])

    transaction_ids = list(set(pm.transaction_id for pm in player_moves))

    txns = Transactions.query \
        .filter(Transactions.transaction_id.in_(transaction_ids)) \
        .filter(Transactions.status == 'complete') \
        .order_by(Transactions.created_at.asc()) \
        .all()

    # Look up player name for context
    player = Players.query.filter_by(sleeper_id=int(player_sleeper_id)).first()
    player_info = None
    if player:
        player_info = {
            'player_id': player.player_id,
            'first_name': player.first_name,
            'last_name': player.last_name,
            'sleeper_id': player.sleeper_id,
            'position': player.position,
        }

    return jsonify(
        success=True,
        player=player_info,
        trade_tree=[t.serialize() for t in txns]
    )


@transactions.route('/transactions/<int:transaction_id>/full_trade_tree', methods=['GET', 'OPTIONS'])
def get_full_trade_tree(transaction_id):
    """
    Given a transaction, build a trade tree showing the ripple effect for each
    team involved. Returns transactions grouped by team in chronological order,
    tracking what happened to each asset that changed hands.

    Response structure:
    {
        origin: {...},                    # The original transaction
        teams: {
            <sleeper_roster_id>: {
                team_id: ...,
                team_name: ...,
                sleeper_roster_id: ...,
                acquired: [...],          # Players/picks acquired in origin
                transactions: [...]       # Subsequent transactions in chrono order
            },
            ...
        }
    }
    """
    # Get the original transaction
    origin = Transactions.query.get(transaction_id)
    if not origin:
        return jsonify(success=False, error='Transaction not found'), 404

    # Get all player moves in the original transaction
    origin_player_moves = TransactionPlayers.query \
        .filter_by(transaction_id=transaction_id) \
        .all()

    # Get all draft pick moves in the original transaction
    from app.models.transaction_draft_picks import TransactionDraftPicks
    origin_pick_moves = TransactionDraftPicks.query \
        .filter_by(transaction_id=transaction_id) \
        .all()

    if not origin_player_moves and not origin_pick_moves:
        return jsonify(success=True, origin=origin.serialize(), teams={})

    # Get rosters involved in the original transaction
    origin_rosters = TransactionRosters.query \
        .filter_by(transaction_id=transaction_id) \
        .all()

    # Build team info lookup
    teams_data = {}
    for roster in origin_rosters:
        team = Teams.query.filter_by(sleeper_roster_id=roster.sleeper_roster_id).first()
        teams_data[roster.sleeper_roster_id] = {
            'team_id': team.team_id if team else None,
            'team_name': team.team_name if team else f'Roster {roster.sleeper_roster_id}',
            'sleeper_roster_id': roster.sleeper_roster_id,
            'acquired_players': [],
            'acquired_picks': [],
            'transactions': []
        }

    # Track which players went to which team (add = acquired)
    player_to_team = {}  # player_sleeper_id -> sleeper_roster_id that acquired them
    for move in origin_player_moves:
        if move.action == 'add':
            player_to_team[move.player_sleeper_id] = move.sleeper_roster_id
            # Add player info to team's acquired list
            player = Players.query.filter_by(sleeper_id=int(move.player_sleeper_id)).first()
            player_info = {
                'sleeper_id': move.player_sleeper_id,
                'first_name': player.first_name if player else 'Unknown',
                'last_name': player.last_name if player else f'(ID: {move.player_sleeper_id})',
                'position': player.position if player else None,
            }
            if move.sleeper_roster_id in teams_data:
                teams_data[move.sleeper_roster_id]['acquired_players'].append(player_info)

    # Track which picks went to which team
    # Key: (season, round, roster_id) - roster_id is whose pick it originally is
    # owner_id = who RECEIVES the pick in this trade (new holder)
    # previous_owner_id = who GAVE the pick away
    # roster_id = whose pick it originally is
    pick_to_team = {}  # pick_key -> sleeper_roster_id that currently holds it
    origin_pick_keys = []
    for pick in origin_pick_moves:
        pick_key = (pick.season, pick.round, pick.roster_id)
        pick_to_team[pick_key] = pick.owner_id
        origin_pick_keys.append(pick_key)
        pick_info = {
            'season': pick.season,
            'round': pick.round,
            'original_owner_id': pick.roster_id,
        }
        if pick.owner_id in teams_data:
            teams_data[pick.owner_id]['acquired_picks'].append(pick_info)

    # Get only the player sleeper IDs that were ACQUIRED in the origin transaction
    # We only care about tracking assets that changed hands, not players that were dropped
    player_sleeper_ids = list(player_to_team.keys())

    # Find all subsequent transactions involving these players
    subsequent_player_moves = []
    if player_sleeper_ids:
        subsequent_player_moves = TransactionPlayers.query \
            .filter(TransactionPlayers.player_sleeper_id.in_(player_sleeper_ids)) \
            .join(Transactions) \
            .filter(Transactions.status == 'complete') \
            .filter(Transactions.created_at > origin.created_at) \
            .order_by(Transactions.created_at.asc()) \
            .all()

    # Find all subsequent transactions involving tracked draft picks
    subsequent_pick_moves = []
    if origin_pick_keys:
        # Query for picks that match our tracked (season, round, roster_id) combos
        from sqlalchemy import or_, and_
        pick_conditions = [
            and_(
                TransactionDraftPicks.season == pk[0],
                TransactionDraftPicks.round == pk[1],
                TransactionDraftPicks.roster_id == pk[2]
            )
            for pk in origin_pick_keys
        ]
        subsequent_pick_moves = TransactionDraftPicks.query \
            .filter(or_(*pick_conditions)) \
            .join(Transactions) \
            .filter(Transactions.status == 'complete') \
            .filter(Transactions.created_at > origin.created_at) \
            .order_by(Transactions.created_at.asc()) \
            .all()

    # Collect all subsequent transaction IDs from both players and picks
    subsequent_txn_ids = set()
    for move in subsequent_player_moves:
        subsequent_txn_ids.add(move.transaction_id)
    for move in subsequent_pick_moves:
        subsequent_txn_ids.add(move.transaction_id)

    # Load all subsequent transactions ordered chronologically
    subsequent_txns = []
    if subsequent_txn_ids:
        subsequent_txns = Transactions.query \
            .filter(Transactions.transaction_id.in_(subsequent_txn_ids)) \
            .order_by(Transactions.created_at.asc()) \
            .all()

    # Group subsequent transactions by which team's "branch" they belong to
    # A transaction belongs to a team's branch if they were the last known holder
    # of any player/pick involved

    # Current holder tracking
    current_player_holder = dict(player_to_team)  # player_sleeper_id -> roster_id
    current_pick_holder = dict(pick_to_team)      # pick_key -> roster_id

    # Process transactions in chronological order
    for txn in subsequent_txns:
        txn_id = txn.transaction_id
        txn_data = txn.serialize()

        # Get all player and pick moves in this transaction
        txn_player_moves = TransactionPlayers.query.filter_by(transaction_id=txn_id).all()
        txn_pick_moves = TransactionDraftPicks.query.filter_by(transaction_id=txn_id).all()

        # Find which "branch" this transaction belongs to
        involved_branches = set()

        # Check players
        for tm in txn_player_moves:
            if tm.player_sleeper_id in current_player_holder:
                involved_branches.add(current_player_holder[tm.player_sleeper_id])

        # Check picks
        for pm in txn_pick_moves:
            pick_key = (pm.season, pm.round, pm.roster_id)
            if pick_key in current_pick_holder:
                involved_branches.add(current_pick_holder[pick_key])

        # Add this transaction to all involved team branches
        for branch_roster_id in involved_branches:
            if branch_roster_id in teams_data:
                teams_data[branch_roster_id]['transactions'].append(txn_data)

        # Update current holders based on this transaction
        for tm in txn_player_moves:
            if tm.action == 'add' and tm.player_sleeper_id in current_player_holder:
                current_player_holder[tm.player_sleeper_id] = tm.sleeper_roster_id

        for pm in txn_pick_moves:
            pick_key = (pm.season, pm.round, pm.roster_id)
            if pick_key in current_pick_holder:
                current_pick_holder[pick_key] = pm.owner_id

    return jsonify(
        success=True,
        origin=origin.serialize(),
        teams=teams_data
    )
