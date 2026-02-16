import logging
from collections import defaultdict
from sqlalchemy import or_, and_
from app.models.transactions import Transactions
from app.models.transaction_players import TransactionPlayers
from app.models.transaction_rosters import TransactionRosters
from app.models.transaction_draft_picks import TransactionDraftPicks
from app.models.teams import Teams
from app.models.players import Players
from app.models.draft_picks import DraftPicks


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

    # 1. Get origin transaction details
    origin_player_moves = TransactionPlayers.query.filter_by(transaction_id=transaction_id).all()
    origin_pick_moves = TransactionDraftPicks.query.filter_by(transaction_id=transaction_id).all()
    origin_rosters = TransactionRosters.query.filter_by(transaction_id=transaction_id).all()
    
    if not origin_player_moves and not origin_pick_moves:
        return origin, {}

    # 2. Initialize Branch Data
    teams_data = {}
    # Map roster_id -> Set of active tracked asset keys
    # Asset Keys: "player:<sleeper_id>" or "pick:<season>:<round>:<org_owner>"
    branch_active_assets = defaultdict(set)
    branch_roster_ids = []

    for roster in origin_rosters:
        rid = roster.sleeper_roster_id
        branch_roster_ids.append(rid)
        
        team = Teams.query.filter_by(sleeper_roster_id=rid).first()
        teams_data[rid] = {
            'team_id': team.team_id if team else None,
            'team_name': team.team_name if team else f'Roster {rid}',
            'sleeper_roster_id': rid,
            'acquired_players': [],
            'acquired_picks': [],
            'transactions': []
        }

    # 3. Populate Initial Acquisitions (Active Assets)
    # Batch player lookup
    acquired_player_ids = [m.player_sleeper_id for m in origin_player_moves if m.action == 'add']
    players_lookup = {}
    if acquired_player_ids:
        for p in Players.query.filter(Players.sleeper_id.in_(acquired_player_ids)).all():
            players_lookup[p.sleeper_id] = p

    for move in origin_player_moves:
        if move.action == 'add' and move.sleeper_roster_id in teams_data:
            rid = move.sleeper_roster_id
            player = players_lookup.get(move.player_sleeper_id)
            
            # Record initial acquisition
            teams_data[rid]['acquired_players'].append({
                'sleeper_id': move.player_sleeper_id,
                'first_name': player.first_name if player else 'Unknown',
                'last_name': player.last_name if player else f'(ID: {move.player_sleeper_id})',
                'position': player.position if player else None,
            })
            
            # Mark as active for this branch
            branch_active_assets[rid].add(f"player:{move.player_sleeper_id}")

    for pick in origin_pick_moves:
        if pick.owner_id in teams_data:
            rid = pick.owner_id
            
            # Check draft status
            drafted_player = None
            draft_pick = DraftPicks.query.filter_by(
                season=pick.season,
                round=pick.round,
                original_roster_id=pick.roster_id,
                type='rookie'
            ).first()
            
            pick_no = None
            if draft_pick:
                pick_no = draft_pick.pick_no
                if draft_pick.player_sleeper_id:
                     dp_player = Players.query.filter_by(sleeper_id=draft_pick.player_sleeper_id).first()
                     if dp_player:
                         drafted_player = {
                            'sleeper_id': dp_player.sleeper_id,
                            'first_name': dp_player.first_name,
                            'last_name': dp_player.last_name,
                            'position': dp_player.position,
                         }

            # Record initial acquisition
            teams_data[rid]['acquired_picks'].append({
                'season': pick.season,
                'round': pick.round,
                'original_owner_id': pick.roster_id,
                'pick_no': pick_no,
                'drafted_player': drafted_player
            })
            
            # Mark as active (Note: we don't automatically convert to player here yet)
            branch_active_assets[rid].add(f"pick:{pick.season}:{pick.round}:{pick.roster_id}")


    # 4. Fetch ALL future transactions for these rosters
    if not branch_roster_ids:
        return origin, teams_data

    # We fetch potentially relevant transactions: those created after origin, involving our rosters
    future_txns = Transactions.query \
        .join(TransactionRosters) \
        .filter(TransactionRosters.sleeper_roster_id.in_(branch_roster_ids)) \
        .filter(Transactions.created_at > origin.created_at) \
        .filter(Transactions.status == 'complete') \
        .order_by(Transactions.created_at.asc()) \
        .all()

    # Deduplicate by ID (one txn might involve multiple branches, which is fine, but result list is unique txns)
    # We iterate linearly.
    
    # Pre-fetch move data to avoid N+1
    txn_ids = [t.transaction_id for t in future_txns]
    
    txn_player_moves_map = defaultdict(list)
    txn_pick_moves_map = defaultdict(list)
    txn_roster_map = defaultdict(list) # To know which rosters are involved in each txn

    if txn_ids:
        # Batch Fetch
        chunk_size = 500
        for i in range(0, len(txn_ids), chunk_size):
            chunk = txn_ids[i:i+chunk_size]
            
            for pm in TransactionPlayers.query.filter(TransactionPlayers.transaction_id.in_(chunk)).all():
                txn_player_moves_map[pm.transaction_id].append(pm)
                
            for dp in TransactionDraftPicks.query.filter(TransactionDraftPicks.transaction_id.in_(chunk)).all():
                txn_pick_moves_map[dp.transaction_id].append(dp)
            
            for tr in TransactionRosters.query.filter(TransactionRosters.transaction_id.in_(chunk)).all():
                txn_roster_map[tr.transaction_id].append(tr.sleeper_roster_id)

    # 5. Process Timeline
    
    for txn in future_txns:
        tid = txn.transaction_id
        involved_rosters = txn_roster_map[tid]
        
        # For each branch involved in this transaction, checks if it affects their assets
        relevant_to_branches = set()
        
        for rid in involved_rosters:
            if rid not in branch_active_assets: 
                continue 
                
            active_assets = branch_active_assets[rid]
            if not active_assets:
                continue 
            
            # Check Players
            moves = txn_player_moves_map[tid]
            affected = False
            
            # Assets given up (Players)
            players_given = [m for m in moves if m.sleeper_roster_id == rid and m.action == 'drop']
            for pm in players_given:
                key = f"player:{pm.player_sleeper_id}"
                if key in active_assets:
                    affected = True
                    active_assets.remove(key)
            
            # Assets given up (Picks)
            picks_given = [p for p in txn_pick_moves_map[tid] if p.previous_owner_id == rid]
            for dp in picks_given:
                key = f"pick:{dp.season}:{dp.round}:{dp.roster_id}"
                if key in active_assets:
                    affected = True
                    active_assets.remove(key)
            
            if affected:
                relevant_to_branches.add(rid)

                # Track what was acquired in return (trades, waivers, free agent moves)
                # Players Acquired
                players_acquired = [m for m in moves if m.sleeper_roster_id == rid and m.action == 'add']
                for pm in players_acquired:
                    branch_active_assets[rid].add(f"player:{pm.player_sleeper_id}")

                # Picks Acquired (only relevant for trades)
                if txn.type == 'trade':
                    picks_acquired = [p for p in txn_pick_moves_map[tid] if p.owner_id == rid]
                    for dp in picks_acquired:
                        k = f"pick:{dp.season}:{dp.round}:{dp.roster_id}"
                        branch_active_assets[rid].add(k)

        # If transaction was relevant to any branch, add it to their history
        if relevant_to_branches:
            serialized_txn = txn.serialize()
            for rid in relevant_to_branches:
                teams_data[rid]['transactions'].append(serialized_txn)

    # 6. Fetch Draft Results for ALL involved picks
    # The set of relevant picks are those in `origin_pick_moves` AND any pick in `future_txns` that was acquired by our branches.
    
    relevant_picks = set()
    
    # Origin picks
    for p in origin_pick_moves:
        relevant_picks.add((p.season, p.round, p.roster_id))
        
    # Future relevant picks
    for txn in future_txns:
        if txn.transaction_id in txn_pick_moves_map:
            for p in txn_pick_moves_map[txn.transaction_id]:
                # If this pick moved to/from one of our tracked branches, it's relevant
                if p.owner_id in teams_data or p.previous_owner_id in teams_data:
                    relevant_picks.add((p.season, p.round, p.roster_id))

    pick_metadata = {}
    if relevant_picks:
        # Build query filters
        filters = []
        for (season, rnd, rid) in relevant_picks:
            filters.append(and_(
                DraftPicks.season == season,
                DraftPicks.round == rnd,
                DraftPicks.original_roster_id == rid,
                DraftPicks.type == 'rookie'
            ))
        
        # Query DB (optimize with batched ORs)
        picks_info = DraftPicks.query.filter(or_(*filters)).all()
        
        # Pre-fetch players for these picks
        drafted_player_ids = [p.player_sleeper_id for p in picks_info if p.player_sleeper_id]
        draft_players_lookup = {}
        if drafted_player_ids:
            for p in Players.query.filter(Players.sleeper_id.in_(drafted_player_ids)).all():
                draft_players_lookup[p.sleeper_id] = p

        for p in picks_info:
            key = f"{p.season}:{p.round}:{p.original_roster_id}"
            meta = {
                'season': p.season,
                'round': p.round,
                'roster_id': p.original_roster_id,
                'pick_no': p.pick_no,
                'drafted_player': None
            }
            if p.player_sleeper_id and p.player_sleeper_id in draft_players_lookup:
                player = draft_players_lookup[p.player_sleeper_id]
                meta['drafted_player'] = {
                    'sleeper_id': player.sleeper_id,
                    'first_name': player.first_name,
                    'last_name': player.last_name,
                    'position': player.position
                }
            pick_metadata[key] = meta

    return origin, teams_data, pick_metadata
