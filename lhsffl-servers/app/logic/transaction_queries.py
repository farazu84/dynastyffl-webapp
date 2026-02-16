from collections import defaultdict
from sqlalchemy import or_, and_
from app.models.transactions import Transactions
from app.models.transaction_players import TransactionPlayers
from app.models.transaction_rosters import TransactionRosters
from app.models.transaction_draft_picks import TransactionDraftPicks
from app.models.teams import Teams
from app.models.players import Players


def get_trade_tree(player_sleeper_id):
    """
    Get the trade tree for a player: all transactions where this player was
    added or dropped, ordered chronologically.

    Returns (player_info, transactions) where player_info may be None.
    """
    player_moves = TransactionPlayers.query \
        .filter_by(player_sleeper_id=player_sleeper_id) \
        .all()

    if not player_moves:
        return None, []

    transaction_ids = list(set(pm.transaction_id for pm in player_moves))

    txns = Transactions.query \
        .filter(Transactions.transaction_id.in_(transaction_ids)) \
        .filter(Transactions.status == 'complete') \
        .order_by(Transactions.created_at.asc()) \
        .all()

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

    return player_info, txns


def get_full_trade_tree(transaction_id):
    """
    Given a transaction, build a trade tree showing the ripple effect for each
    team involved. Returns (origin, teams_data) or (None, None) if not found.

    Response structure for teams_data:
    {
        <sleeper_roster_id>: {
            team_id: ...,
            team_name: ...,
            sleeper_roster_id: ...,
            acquired_players: [...],
            acquired_picks: [...],
            transactions: [...]
        },
        ...
    }
    """
    origin = Transactions.query.get(transaction_id)
    if not origin:
        return None, None

    # Get all player and pick moves in the original transaction
    origin_player_moves = TransactionPlayers.query \
        .filter_by(transaction_id=transaction_id) \
        .all()
    origin_pick_moves = TransactionDraftPicks.query \
        .filter_by(transaction_id=transaction_id) \
        .all()

    if not origin_player_moves and not origin_pick_moves:
        return origin, {}

    # Get rosters involved and build team info lookup
    origin_rosters = TransactionRosters.query \
        .filter_by(transaction_id=transaction_id) \
        .all()

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
    player_to_team = {}
    # Batch-load player info for all acquired players
    acquired_player_ids = [m.player_sleeper_id for m in origin_player_moves if m.action == 'add']
    players_lookup = {}
    if acquired_player_ids:
        players = Players.query.filter(Players.sleeper_id.in_(acquired_player_ids)).all()
        players_lookup = {p.sleeper_id: p for p in players}

    for move in origin_player_moves:
        if move.action == 'add':
            player_to_team[move.player_sleeper_id] = move.sleeper_roster_id
            player = players_lookup.get(move.player_sleeper_id)
            player_info = {
                'sleeper_id': move.player_sleeper_id,
                'first_name': player.first_name if player else 'Unknown',
                'last_name': player.last_name if player else f'(ID: {move.player_sleeper_id})',
                'position': player.position if player else None,
            }
            if move.sleeper_roster_id in teams_data:
                teams_data[move.sleeper_roster_id]['acquired_players'].append(player_info)

    # Track which picks went to which team
    pick_to_team = {}
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

    # Collect all subsequent transaction IDs
    subsequent_txn_ids = set()
    for move in subsequent_player_moves:
        subsequent_txn_ids.add(move.transaction_id)
    for move in subsequent_pick_moves:
        subsequent_txn_ids.add(move.transaction_id)

    # Load all subsequent transactions
    subsequent_txns = []
    if subsequent_txn_ids:
        subsequent_txns = Transactions.query \
            .filter(Transactions.transaction_id.in_(subsequent_txn_ids)) \
            .order_by(Transactions.created_at.asc()) \
            .all()

    # Batch-load all player and pick moves for subsequent transactions (fix N+1)
    all_txn_player_moves = defaultdict(list)
    all_txn_pick_moves = defaultdict(list)
    if subsequent_txn_ids:
        for move in TransactionPlayers.query.filter(
            TransactionPlayers.transaction_id.in_(subsequent_txn_ids)
        ).all():
            all_txn_player_moves[move.transaction_id].append(move)

        for move in TransactionDraftPicks.query.filter(
            TransactionDraftPicks.transaction_id.in_(subsequent_txn_ids)
        ).all():
            all_txn_pick_moves[move.transaction_id].append(move)

    # Current holder tracking
    current_player_holder = dict(player_to_team)
    current_pick_holder = dict(pick_to_team)

    # Process transactions in chronological order
    for txn in subsequent_txns:
        txn_id = txn.transaction_id
        txn_data = txn.serialize()

        txn_player_moves = all_txn_player_moves[txn_id]
        txn_pick_moves = all_txn_pick_moves[txn_id]

        # Find which "branch" this transaction belongs to
        involved_branches = set()
        for tm in txn_player_moves:
            if tm.player_sleeper_id in current_player_holder:
                involved_branches.add(current_player_holder[tm.player_sleeper_id])
        for pm in txn_pick_moves:
            pick_key = (pm.season, pm.round, pm.roster_id)
            if pick_key in current_pick_holder:
                involved_branches.add(current_pick_holder[pick_key])

        for branch_roster_id in involved_branches:
            if branch_roster_id in teams_data:
                teams_data[branch_roster_id]['transactions'].append(txn_data)

        # Update current holders
        for tm in txn_player_moves:
            if tm.action == 'add' and tm.player_sleeper_id in current_player_holder:
                current_player_holder[tm.player_sleeper_id] = tm.sleeper_roster_id
        for pm in txn_pick_moves:
            pick_key = (pm.season, pm.round, pm.roster_id)
            if pick_key in current_pick_holder:
                current_pick_holder[pick_key] = pm.owner_id

    return origin, teams_data
