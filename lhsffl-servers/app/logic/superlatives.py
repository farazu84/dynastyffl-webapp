from sqlalchemy.sql.expression import func
from app import db
from app.models.transactions import Transactions
from app.models.transaction_players import TransactionPlayers
from app.models.transaction_rosters import TransactionRosters
from app.models.transaction_draft_picks import TransactionDraftPicks
from app.models.draft_picks import DraftPicks
from app.models.teams import Teams
from app.models.players import Players


def _build_player_lookup(sleeper_ids):
    """Batch-load players by sleeper_id and return a lookup dict."""
    if not sleeper_ids:
        return {}
    players = Players.query.filter(Players.sleeper_id.in_(sleeper_ids)).all()
    return {p.sleeper_id: p for p in players}


def _build_team_lookup(roster_ids):
    """Batch-load teams by sleeper_roster_id and return a lookup dict."""
    if not roster_ids:
        return {}
    teams = Teams.query.filter(Teams.sleeper_roster_id.in_(roster_ids)).all()
    return {t.sleeper_roster_id: t for t in teams}


def _player_info(player, sleeper_id):
    """Build a standard player info dict from a Player object (or None)."""
    return {
        'player_sleeper_id': sleeper_id,
        'first_name': player.first_name if player else 'Unknown',
        'last_name': player.last_name if player else str(sleeper_id),
        'position': player.position if player else None,
    }


def get_player_superlatives():
    """
    Player superlatives:
    - most_traded: players involved in the most trades
    - most_teams: players rostered on the most different fantasy teams
    - most_dropped: players dropped the most times
    - boomerang: players added to the same team multiple times
    """

    # Most traded players
    most_traded = db.session.query(
        TransactionPlayers.player_sleeper_id,
        func.count(func.distinct(TransactionPlayers.transaction_id)).label('trade_count')
    ) \
        .join(Transactions) \
        .filter(Transactions.type == 'trade', Transactions.status == 'complete') \
        .group_by(TransactionPlayers.player_sleeper_id) \
        .order_by(func.count(func.distinct(TransactionPlayers.transaction_id)).desc()) \
        .limit(10) \
        .all()

    # Most teams rostered
    most_teams = db.session.query(
        TransactionPlayers.player_sleeper_id,
        func.count(func.distinct(TransactionPlayers.sleeper_roster_id)).label('team_count')
    ) \
        .join(Transactions) \
        .filter(TransactionPlayers.action == 'add', Transactions.status == 'complete') \
        .group_by(TransactionPlayers.player_sleeper_id) \
        .order_by(func.count(func.distinct(TransactionPlayers.sleeper_roster_id)).desc()) \
        .limit(10) \
        .all()

    # Most dropped players
    most_dropped = db.session.query(
        TransactionPlayers.player_sleeper_id,
        func.count().label('drop_count')
    ) \
        .join(Transactions) \
        .filter(TransactionPlayers.action == 'drop', Transactions.status == 'complete') \
        .group_by(TransactionPlayers.player_sleeper_id) \
        .order_by(func.count().desc()) \
        .limit(10) \
        .all()

    # Boomerang players - added to the same team multiple times
    boomerang_raw = db.session.query(
        TransactionPlayers.player_sleeper_id,
        TransactionPlayers.sleeper_roster_id,
        func.count().label('times_added')
    ) \
        .join(Transactions) \
        .filter(TransactionPlayers.action == 'add', Transactions.status == 'complete') \
        .group_by(TransactionPlayers.player_sleeper_id, TransactionPlayers.sleeper_roster_id) \
        .having(func.count() >= 2) \
        .order_by(func.count().desc()) \
        .limit(10) \
        .all()

    # Batch-load all players referenced across all queries
    all_player_ids = set()
    for pid, _ in most_traded:
        all_player_ids.add(pid)
    for pid, _ in most_teams:
        all_player_ids.add(pid)
    for pid, _ in most_dropped:
        all_player_ids.add(pid)
    for pid, _, _ in boomerang_raw:
        all_player_ids.add(pid)
    players_lookup = _build_player_lookup(list(all_player_ids))

    # Batch-load teams for boomerang
    boomerang_roster_ids = [rid for _, rid, _ in boomerang_raw]
    teams_lookup = _build_team_lookup(boomerang_roster_ids)

    most_traded_result = [
        {**_player_info(players_lookup.get(pid), pid), 'trade_count': count}
        for pid, count in most_traded
    ]

    most_teams_result = [
        {**_player_info(players_lookup.get(pid), pid), 'team_count': count}
        for pid, count in most_teams
    ]

    most_dropped_result = [
        {**_player_info(players_lookup.get(pid), pid), 'drop_count': count}
        for pid, count in most_dropped
    ]

    boomerang_result = []
    for pid, roster_id, times_added in boomerang_raw:
        player = players_lookup.get(pid)
        team = teams_lookup.get(roster_id)
        boomerang_result.append({
            **_player_info(player, pid),
            'team_name': team.team_name if team else f'Roster {roster_id}',
            'times_added': times_added,
        })

    return {
        'most_traded': most_traded_result,
        'most_teams': most_teams_result,
        'most_dropped': most_dropped_result,
        'boomerang': boomerang_result,
    }


def get_team_superlatives():
    """
    Team superlatives:
    - most_trades: teams ranked by total number of trades
    - frequent_trade_partners: pairs of teams that trade with each other the most
    - waiver_warriors: teams with the most waiver/FA pickups
    - draft_capital_movers: teams that have traded the most draft picks
    """

    # Most active traders
    most_trades = db.session.query(
        TransactionRosters.sleeper_roster_id,
        func.count(func.distinct(TransactionRosters.transaction_id)).label('trade_count')
    ) \
        .join(Transactions) \
        .filter(Transactions.type == 'trade', Transactions.status == 'complete') \
        .group_by(TransactionRosters.sleeper_roster_id) \
        .order_by(func.count(func.distinct(TransactionRosters.transaction_id)).desc()) \
        .all()

    # Frequent trade partners
    trade_pairs = db.session.query(
        Transactions.transaction_id,
        TransactionRosters.sleeper_roster_id
    ) \
        .join(TransactionRosters) \
        .filter(Transactions.type == 'trade', Transactions.status == 'complete') \
        .all()

    txn_rosters = {}
    for txn_id, roster_id in trade_pairs:
        txn_rosters.setdefault(txn_id, []).append(roster_id)

    pair_counts = {}
    for txn_id, rosters in txn_rosters.items():
        if len(rosters) >= 2:
            rosters_sorted = sorted(rosters)
            for i in range(len(rosters_sorted)):
                for j in range(i + 1, len(rosters_sorted)):
                    pair = (rosters_sorted[i], rosters_sorted[j])
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1

    sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Waiver wire warriors
    waiver_warriors = db.session.query(
        TransactionPlayers.sleeper_roster_id,
        func.count().label('pickup_count')
    ) \
        .join(Transactions) \
        .filter(
            TransactionPlayers.action == 'add',
            Transactions.type.in_(['waiver', 'free_agent']),
            Transactions.status == 'complete',
        ) \
        .group_by(TransactionPlayers.sleeper_roster_id) \
        .order_by(func.count().desc()) \
        .all()

    # Draft capital movers
    draft_movers = db.session.query(
        TransactionDraftPicks.previous_owner_id,
        func.count().label('picks_traded')
    ) \
        .join(Transactions) \
        .filter(Transactions.type == 'trade', Transactions.status == 'complete') \
        .filter(TransactionDraftPicks.previous_owner_id.isnot(None)) \
        .group_by(TransactionDraftPicks.previous_owner_id) \
        .order_by(func.count().desc()) \
        .all()

    # Batch-load all teams referenced
    all_roster_ids = set()
    for rid, _ in most_trades:
        all_roster_ids.add(rid)
    for (r1, r2), _ in sorted_pairs:
        all_roster_ids.add(r1)
        all_roster_ids.add(r2)
    for rid, _ in waiver_warriors:
        all_roster_ids.add(rid)
    for rid, _ in draft_movers:
        all_roster_ids.add(rid)
    teams_lookup = _build_team_lookup(list(all_roster_ids))

    most_trades_result = [
        {
            'sleeper_roster_id': rid,
            'team_name': teams_lookup[rid].team_name if rid in teams_lookup else f'Roster {rid}',
            'trade_count': count,
        }
        for rid, count in most_trades
    ]

    trade_partners_result = [
        {
            'team_1': teams_lookup[r1].team_name if r1 in teams_lookup else f'Roster {r1}',
            'team_2': teams_lookup[r2].team_name if r2 in teams_lookup else f'Roster {r2}',
            'trade_count': count,
        }
        for (r1, r2), count in sorted_pairs
    ]

    waiver_warriors_result = [
        {
            'sleeper_roster_id': rid,
            'team_name': teams_lookup[rid].team_name if rid in teams_lookup else f'Roster {rid}',
            'pickup_count': count,
        }
        for rid, count in waiver_warriors
    ]

    draft_movers_result = [
        {
            'sleeper_roster_id': rid,
            'team_name': teams_lookup[rid].team_name if rid in teams_lookup else f'Roster {rid}',
            'picks_traded': count,
        }
        for rid, count in draft_movers
    ]

    return {
        'most_trades': most_trades_result,
        'frequent_trade_partners': trade_partners_result,
        'waiver_warriors': waiver_warriors_result,
        'draft_capital_movers': draft_movers_result,
    }


def get_draft_superlatives():
    """
    Draft superlatives:
    - startup_loyalists: players from the startup draft still on their original team
    - startup_steals: latest round startup picks still rostered in the league
    - rookie_draft_steals: lowest picked rookie draft players still on their original team
    """

    startup_picks = DraftPicks.query.filter_by(type='startup').all()

    # Batch-load all players and teams referenced by startup picks
    startup_player_ids = [p.player_sleeper_id for p in startup_picks]
    players_lookup = _build_player_lookup(startup_player_ids)

    loyalists = []
    for pick in startup_picks:
        player = players_lookup.get(pick.player_sleeper_id)
        if not player or player.team_id is None:
            continue
        team = Teams.query.get(player.team_id)
        if not team:
            continue
        if team.sleeper_roster_id == pick.roster_id:
            loyalists.append({
                'player_sleeper_id': pick.player_sleeper_id,
                'first_name': player.first_name,
                'last_name': player.last_name,
                'position': player.position,
                'team_name': team.team_name,
                'round': pick.round,
                'pick_no': pick.pick_no,
            })

    loyalists.sort(key=lambda x: x['pick_no'])

    # Startup steals - latest round startup picks still rostered
    startup_steals = []
    for pick in sorted(startup_picks, key=lambda p: -p.pick_no):
        player = players_lookup.get(pick.player_sleeper_id)
        if not player or player.team_id is None:
            continue
        team = Teams.query.get(player.team_id)
        startup_steals.append({
            'player_sleeper_id': pick.player_sleeper_id,
            'first_name': player.first_name,
            'last_name': player.last_name,
            'position': player.position,
            'team_name': team.team_name if team else 'Unknown',
            'round': pick.round,
            'pick_no': pick.pick_no,
        })
        if len(startup_steals) >= 10:
            break

    # Rookie draft steals
    rookie_picks = DraftPicks.query \
        .filter_by(type='rookie') \
        .order_by(DraftPicks.pick_no.desc()) \
        .all()

    rookie_player_ids = [p.player_sleeper_id for p in rookie_picks]
    rookie_players_lookup = _build_player_lookup(rookie_player_ids)

    rookie_steals = []
    for pick in rookie_picks:
        player = rookie_players_lookup.get(pick.player_sleeper_id)
        if not player or player.team_id is None:
            continue
        team = Teams.query.get(player.team_id)
        if not team:
            continue
        if team.sleeper_roster_id == pick.roster_id:
            rookie_steals.append({
                'player_sleeper_id': pick.player_sleeper_id,
                'first_name': player.first_name,
                'last_name': player.last_name,
                'position': player.position,
                'team_name': team.team_name,
                'season': pick.season,
                'round': pick.round,
                'pick_no': pick.pick_no,
            })
            if len(rookie_steals) >= 10:
                break

    return {
        'startup_loyalists': loyalists,
        'startup_steals': startup_steals,
        'rookie_draft_steals': rookie_steals,
    }
