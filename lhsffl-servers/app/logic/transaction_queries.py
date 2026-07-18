import logging
from collections import defaultdict
from sqlalchemy import or_, and_, func, case
from app import db
from app.models.transactions import Transactions
from app.models.transaction_players import TransactionPlayers
from app.models.transaction_rosters import TransactionRosters
from app.models.transaction_draft_picks import TransactionDraftPicks
from app.models.teams import Teams
from app.models.players import Players
from app.models.draft_picks import DraftPicks
from app.models.player_weekly_stats import PlayerWeeklyStats
from app.models.league_state import LeagueState


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

    txns = Transactions._with_eager_loads(
        Transactions.query
        .filter(Transactions.transaction_id.in_(transaction_ids))
        .filter(Transactions.status == 'complete')
        .order_by(Transactions.created_at.asc())
    ).all()

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


def _build_expansion_selections():
    """
    Map "<feeding_drop_transaction_id>:<player_sleeper_id>" -> {team_name, round, pick_no}
    for every expansion draft selection.

    The "feeding drop" is the latest drop of that player at or before the expansion selection
    date — i.e. the move that sent the player into the expansion pool (the expansion txn's own
    drop for 'atomic' picks, or the prior free_agent drop for 'pre-dropped' picks). Keying on
    that specific transaction lets the trade tree relabel exactly that drop as the selection while
    leaving any later (post-expansion) drop of the same player untouched.
    """
    exp_picks = DraftPicks.query.filter_by(type='expansion').all()
    if not exp_picks:
        return {}

    roster_ids = {p.drafting_roster_id for p in exp_picks}
    team_names = {
        t.sleeper_roster_id: t.team_name
        for t in Teams.query.filter(Teams.sleeper_roster_id.in_(roster_ids)).all()
    }
    player_ids = {p.player_sleeper_id for p in exp_picks}

    # Selection date per player = created_at of the expansion transaction that added them.
    selection_date = {}
    add_rows = db.session.query(
        TransactionPlayers.player_sleeper_id, Transactions.created_at
    ).join(
        Transactions, Transactions.transaction_id == TransactionPlayers.transaction_id
    ).filter(
        Transactions.type == 'expansion',
        TransactionPlayers.action == 'add',
        TransactionPlayers.player_sleeper_id.in_(player_ids),
    ).all()
    for pid, created_at in add_rows:
        selection_date[pid] = created_at

    # All drops of those players; pick the latest one at/before the selection date per player.
    drop_rows = db.session.query(
        TransactionPlayers.player_sleeper_id,
        TransactionPlayers.transaction_id,
        Transactions.created_at,
    ).join(
        Transactions, Transactions.transaction_id == TransactionPlayers.transaction_id
    ).filter(
        TransactionPlayers.action == 'drop',
        TransactionPlayers.player_sleeper_id.in_(player_ids),
    ).all()

    feeding_txn = {}  # player -> (created_at, transaction_id)
    for pid, txn_id, created_at in drop_rows:
        sel = selection_date.get(pid)
        if sel is None or created_at is None:
            continue
        # Feeding drop = the latest drop on or before the selection DAY. Compare by date, not exact
        # timestamp: the synthetic expansion txn is stamped at midnight, while a same-day free_agent
        # drop (the pre-dropped case) happens later that day and must still count as the feeding drop.
        # A genuine post-expansion drop (a later day) is still correctly excluded.
        if created_at.date() > sel.date():
            continue
        best = feeding_txn.get(pid)
        if best is None or created_at >= best[0]:
            feeding_txn[pid] = (created_at, txn_id)

    selections = {}
    for p in exp_picks:
        feeding = feeding_txn.get(p.player_sleeper_id)
        if not feeding:
            continue
        key = f"{feeding[1]}:{p.player_sleeper_id}"
        selections[key] = {
            'team_name': team_names.get(p.drafting_roster_id, f'Roster {p.drafting_roster_id}'),
            'round': p.round,
            'pick_no': p.pick_no,
        }
    return selections


def _attach_production(teams_data, pick_metadata):
    """
    Attach starter-points production analytics to each branch in teams_data (in place).

    Per asset:  teams_data[rid]['production'][player_sleeper_id] =
                  {starter_points, games_started, total_points, ppg}
                — how much that player produced while rostered by this side (branch).
    Per side:   teams_data[rid]['production_totals'] = the rollup across the side's assets.

    Sourced from PlayerWeeklyStats, where sleeper_roster_id is the team that held the player that
    week, so tenure is handled automatically. Only weeks the player started count toward
    starter_points / games_started / ppg; total_points includes bench weeks.
    """
    for rid in teams_data:
        teams_data[rid]['production'] = {}
        teams_data[rid]['production_totals'] = {
            'starter_points': 0.0, 'games_started': 0, 'total_points': 0.0, 'ppg': 0.0,
        }

    # The asset player ids that belong to EACH branch — i.e. exactly the assets that branch displays
    # (initial acquisitions, downstream acquisitions made BY this branch, and the players its picks
    # were used to draft). Crucially this is per-branch: a player from another side's lineage is
    # never counted here just because they happened to be rostered by this team in some unrelated
    # week, which is what was inflating the per-side totals.
    branch_players = {rid: set() for rid in teams_data}
    for rid, data in teams_data.items():
        bp = branch_players[rid]
        for p in data['acquired_players']:
            if p.get('sleeper_id'):
                bp.add(p['sleeper_id'])
        for pk in data['acquired_picks']:
            dp = pk.get('drafted_player')
            if dp and dp.get('sleeper_id'):
                bp.add(dp['sleeper_id'])
        for txn in data['transactions']:
            for pm in (txn.get('player_moves') or []):
                if (pm.get('action') == 'add' and pm.get('sleeper_roster_id') == rid
                        and pm.get('player_sleeper_id')):
                    bp.add(pm['player_sleeper_id'])
            for dpm in (txn.get('draft_pick_moves') or []):
                if dpm.get('owner_id') == rid:
                    meta = pick_metadata.get(
                        f"{dpm.get('season')}:{dpm.get('round')}:{dpm.get('roster_id')}")
                    drafted = meta.get('drafted_player') if meta else None
                    if drafted and drafted.get('sleeper_id'):
                        bp.add(drafted['sleeper_id'])

    all_player_ids = set()
    for bp in branch_players.values():
        all_player_ids |= bp
    roster_ids = list(teams_data.keys())
    if not all_player_ids or not roster_ids:
        return

    filters = [
        PlayerWeeklyStats.player_sleeper_id.in_(all_player_ids),
        PlayerWeeklyStats.sleeper_roster_id.in_(roster_ids),
    ]
    # Only count weeks that have actually been PLAYED. Sleeper pre-populates the upcoming season's
    # weeks with the set lineup and 0 points, so without this bound those unplayed weeks would be
    # counted as games started (e.g. an upcoming season inflating GS by ~18 and tanking PPG).
    league_state = LeagueState.query.filter_by(current=True).first()
    if league_state:
        filters.append(or_(
            PlayerWeeklyStats.year < league_state.year,
            and_(PlayerWeeklyStats.year == league_state.year,
                 PlayerWeeklyStats.week < league_state.week),
        ))

    rows = db.session.query(
        PlayerWeeklyStats.player_sleeper_id,
        PlayerWeeklyStats.sleeper_roster_id,
        func.sum(case((PlayerWeeklyStats.is_starter.is_(True), PlayerWeeklyStats.points), else_=0)),
        func.sum(case((PlayerWeeklyStats.is_starter.is_(True), 1), else_=0)),
        func.sum(PlayerWeeklyStats.points),
    ).filter(
        *filters
    ).group_by(
        PlayerWeeklyStats.player_sleeper_id,
        PlayerWeeklyStats.sleeper_roster_id,
    ).all()

    prod_by_pair = {}
    for player_id, rid, starter_points, games_started, total_points in rows:
        sp = round(float(starter_points or 0), 1)
        gs = int(games_started or 0)
        tp = round(float(total_points or 0), 1)
        prod_by_pair[(player_id, rid)] = {
            'starter_points': sp,
            'games_started': gs,
            'total_points': tp,
            'ppg': round(sp / gs, 1) if gs else 0.0,
        }

    # Attribute production to a branch ONLY for that branch's own asset players, on that roster.
    for rid in teams_data:
        totals = teams_data[rid]['production_totals']
        for player_id in branch_players[rid]:
            entry = prod_by_pair.get((player_id, rid))
            if not entry:
                continue
            teams_data[rid]['production'][player_id] = entry
            totals['starter_points'] += entry['starter_points']
            totals['games_started'] += entry['games_started']
            totals['total_points'] += entry['total_points']
        totals['starter_points'] = round(totals['starter_points'], 1)
        totals['total_points'] = round(totals['total_points'], 1)
        totals['ppg'] = (round(totals['starter_points'] / totals['games_started'], 1)
                         if totals['games_started'] else 0.0)


def get_full_trade_tree(transaction_id):
    """
    Given a transaction, build a trade tree showing the ripple effect for each
    team involved. Returns (origin, teams_data, pick_metadata, expansion_selections) or
    (None, None, None, None) if not found.

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
        return None, None, None, None

    expansion_selections = _build_expansion_selections()

    # 1. Get origin transaction details
    origin_player_moves = TransactionPlayers.query.filter_by(transaction_id=transaction_id).all()
    origin_pick_moves = TransactionDraftPicks.query.filter_by(transaction_id=transaction_id).all()
    origin_rosters = TransactionRosters.query.filter_by(transaction_id=transaction_id).all()
    
    if not origin_player_moves and not origin_pick_moves:
        return origin, {}, {}, expansion_selections

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
        return origin, teams_data, {}, expansion_selections

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

    _attach_production(teams_data, pick_metadata)

    return origin, teams_data, pick_metadata, expansion_selections
