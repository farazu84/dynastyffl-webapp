import time
from functools import wraps
from sqlalchemy import tuple_
from sqlalchemy.sql.expression import func
from app import db
from app.models.transactions import Transactions
from app.models.transaction_players import TransactionPlayers
from app.models.transaction_rosters import TransactionRosters
from app.models.transaction_draft_picks import TransactionDraftPicks
from app.models.draft_picks import DraftPicks
from app.models.teams import Teams
from app.models.players import Players
from app.models.matchups import Matchups
from app.models.playoff_matchups import PlayoffMatchups
from app.models.player_weekly_stats import PlayerWeeklyStats


def timed_cache(seconds=3600):
    """Simple time-based cache decorator. No external dependencies."""
    def decorator(func):
        cache = {}
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if 'result' in cache and now - cache['time'] < seconds:
                return cache['result']
            result = func(*args, **kwargs)
            cache['result'] = result
            cache['time'] = now
            return result
        return wrapper
    return decorator


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


def _build_team_lookup_by_id(team_ids):
    """Batch-load teams by team_id and return a lookup dict."""
    if not team_ids:
        return {}
    teams = Teams.query.filter(Teams.team_id.in_(team_ids)).all()
    return {t.team_id: t for t in teams}


def _player_info(player, sleeper_id):
    """Build a standard player info dict from a Player object (or None)."""
    return {
        'player_sleeper_id': sleeper_id,
        'first_name': player.first_name if player else 'Unknown',
        'last_name': player.last_name if player else str(sleeper_id),
        'position': player.position if player else None,
    }


def _by_position(items, n=5):
    """Partition an already-sorted list into {position: [top-n]} dict."""
    by_pos = {}
    for item in items:
        pos = item.get('position')
        if pos:
            lst = by_pos.setdefault(pos, [])
            if len(lst) < n:
                lst.append(item)
    return by_pos


@timed_cache(seconds=3600)
def get_player_superlatives():
    """
    Player superlatives:
    - most_traded: players involved in the most trades
    - most_teams: players rostered on the most different fantasy teams
    - most_dropped: players dropped the most times
    - boomerang: players added to the same team multiple times
    """

    # Most traded players
    most_traded_raw = db.session.query(
        TransactionPlayers.player_sleeper_id,
        func.count(func.distinct(TransactionPlayers.transaction_id)).label('trade_count'),
        Players.position, Players.first_name, Players.last_name,
    ) \
        .join(Transactions) \
        .join(Players, Players.sleeper_id == TransactionPlayers.player_sleeper_id) \
        .filter(Transactions.type == 'trade', Transactions.status == 'complete') \
        .group_by(TransactionPlayers.player_sleeper_id, Players.position, Players.first_name, Players.last_name) \
        .order_by(func.count(func.distinct(TransactionPlayers.transaction_id)).desc()) \
        .all()

    # Most teams rostered
    most_teams_raw = db.session.query(
        TransactionPlayers.player_sleeper_id,
        func.count(func.distinct(TransactionPlayers.sleeper_roster_id)).label('team_count'),
        Players.position, Players.first_name, Players.last_name,
    ) \
        .join(Transactions) \
        .join(Players, Players.sleeper_id == TransactionPlayers.player_sleeper_id) \
        .filter(TransactionPlayers.action == 'add', Transactions.status == 'complete') \
        .group_by(TransactionPlayers.player_sleeper_id, Players.position, Players.first_name, Players.last_name) \
        .order_by(func.count(func.distinct(TransactionPlayers.sleeper_roster_id)).desc()) \
        .all()

    # Most dropped players
    most_dropped_raw = db.session.query(
        TransactionPlayers.player_sleeper_id,
        func.count().label('drop_count'),
        Players.position, Players.first_name, Players.last_name,
    ) \
        .join(Transactions) \
        .join(Players, Players.sleeper_id == TransactionPlayers.player_sleeper_id) \
        .filter(TransactionPlayers.action == 'drop', Transactions.status == 'complete') \
        .group_by(TransactionPlayers.player_sleeper_id, Players.position, Players.first_name, Players.last_name) \
        .order_by(func.count().desc()) \
        .all()

    # Boomerang players - added to the same team multiple times
    boomerang_raw = db.session.query(
        TransactionPlayers.player_sleeper_id,
        TransactionPlayers.sleeper_roster_id,
        func.count().label('times_added'),
        Players.position, Players.first_name, Players.last_name,
    ) \
        .join(Transactions) \
        .join(Players, Players.sleeper_id == TransactionPlayers.player_sleeper_id) \
        .filter(TransactionPlayers.action == 'add', Transactions.status == 'complete') \
        .group_by(TransactionPlayers.player_sleeper_id, TransactionPlayers.sleeper_roster_id, Players.position, Players.first_name, Players.last_name) \
        .having(func.count() >= 2) \
        .order_by(func.count().desc()) \
        .all()

    # Batch-load teams for boomerang (still needed since team name isn't in the join)
    boomerang_roster_ids = [r.sleeper_roster_id for r in boomerang_raw]
    teams_lookup = _build_team_lookup(boomerang_roster_ids)

    most_traded_result = [
        {'player_sleeper_id': r.player_sleeper_id, 'first_name': r.first_name, 'last_name': r.last_name, 'position': r.position, 'trade_count': r.trade_count}
        for r in most_traded_raw
    ]

    most_teams_result = [
        {'player_sleeper_id': r.player_sleeper_id, 'first_name': r.first_name, 'last_name': r.last_name, 'position': r.position, 'team_count': r.team_count}
        for r in most_teams_raw
    ]

    most_dropped_result = [
        {'player_sleeper_id': r.player_sleeper_id, 'first_name': r.first_name, 'last_name': r.last_name, 'position': r.position, 'drop_count': r.drop_count}
        for r in most_dropped_raw
    ]

    boomerang_result = [
        {
            'player_sleeper_id': r.player_sleeper_id,
            'first_name': r.first_name,
            'last_name': r.last_name,
            'position': r.position,
            'team_name': teams_lookup.get(r.sleeper_roster_id).team_name if teams_lookup.get(r.sleeper_roster_id) else f'Roster {r.sleeper_roster_id}',
            'times_added': r.times_added,
        }
        for r in boomerang_raw
    ]

    return {
        'most_traded': most_traded_result[:5],
        'most_traded_by_position': _by_position(most_traded_result),
        'most_teams': most_teams_result[:5],
        'most_teams_by_position': _by_position(most_teams_result),
        'most_dropped': most_dropped_result[:5],
        'most_dropped_by_position': _by_position(most_dropped_result),
        'boomerang': boomerang_result[:5],
        'boomerang_by_position': _by_position(boomerang_result),
    }


@timed_cache(seconds=3600)
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


@timed_cache(seconds=3600)
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

    # Batch-load all teams by team_id (avoids N+1 Teams.query.get per loop)
    all_team_ids = set(
        p.team_id for p in players_lookup.values() if p.team_id is not None
    )
    teams_by_id = _build_team_lookup_by_id(list(all_team_ids))

    loyalists = []
    for pick in startup_picks:
        player = players_lookup.get(pick.player_sleeper_id)
        if not player or player.team_id is None:
            continue
        team = teams_by_id.get(player.team_id)
        if not team:
            continue
        if team.sleeper_roster_id == pick.drafting_roster_id:
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
        team = teams_by_id.get(player.team_id)
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

    # Batch-load teams for rookie players
    rookie_team_ids = set(
        p.team_id for p in rookie_players_lookup.values() if p.team_id is not None
    )
    rookie_teams_by_id = _build_team_lookup_by_id(list(rookie_team_ids))

    rookie_steals = []
    for pick in rookie_picks:
        player = rookie_players_lookup.get(pick.player_sleeper_id)
        if not player or player.team_id is None:
            continue
        team = rookie_teams_by_id.get(player.team_id)
        if not team:
            continue
        if team.sleeper_roster_id == pick.drafting_roster_id:
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
        'startup_loyalists': loyalists[:5],
        'startup_loyalists_by_position': _by_position(loyalists),
        'startup_steals': startup_steals[:5],
        'startup_steals_by_position': _by_position(startup_steals),
        'rookie_draft_steals': rookie_steals[:5],
        'rookie_draft_steals_by_position': _by_position(rookie_steals),
    }


def _played_year_weeks():
    """(year, week) pairs that have actually been played — i.e. have a completed
    matchup. Used to exclude future/unplayed weeks from per-player stats: Sleeper
    pre-populates the upcoming season's schedule with zero-point roster rows, which
    would otherwise inflate start counts and drag scoring averages to 0."""
    rows = (db.session.query(Matchups.year, Matchups.week)
            .filter(Matchups.completed.is_(True))
            .distinct().all())
    return [(y, w) for y, w in rows]


def _team_namer(roster_ids):
    """Return a (roster_id -> team_name) resolver function for the given ids."""
    lookup = _build_team_lookup(list(roster_ids))

    def name(rid):
        team = lookup.get(rid)
        return team.team_name if team else f'Roster {rid}'

    return name


@timed_cache(seconds=3600)
def get_scoring_superlatives():
    """
    Scoring superlatives:
    - nuke: highest single-week team score ever
    - robbed: most points ever scored in a loss
    - the_franchise: player with the most career fantasy points (starter + bench)
    """

    # Nuke — highest single-week team score.
    nuke_rows = Matchups.query.filter(Matchups.completed.is_(True)) \
        .order_by(Matchups.points_for.desc()).limit(5).all()

    # Robbed — most points scored in a loss.
    robbed_rows = Matchups.query.filter(
        Matchups.completed.is_(True),
        Matchups.points_for < Matchups.points_against,
    ).order_by(Matchups.points_for.desc()).limit(5).all()

    roster_ids = set()
    for m in nuke_rows + robbed_rows:
        roster_ids.add(m.sleeper_roster_id)
        roster_ids.add(m.opponent_sleeper_roster_id)
    team_name = _team_namer(roster_ids)

    nuke = [{
        'team_name': team_name(m.sleeper_roster_id),
        'opponent_name': team_name(m.opponent_sleeper_roster_id),
        'year': m.year, 'week': m.week,
        'points': round(m.points_for, 1),
    } for m in nuke_rows]

    robbed = [{
        'team_name': team_name(m.sleeper_roster_id),
        'opponent_name': team_name(m.opponent_sleeper_roster_id),
        'year': m.year, 'week': m.week,
        'points': round(m.points_for, 1),
        'points_against': round(m.points_against, 1),
    } for m in robbed_rows]

    # The Franchise — most career fantasy points across the league.
    played = _played_year_weeks()
    franchise_raw = db.session.query(
        PlayerWeeklyStats.player_sleeper_id,
        func.sum(PlayerWeeklyStats.points).label('total_points'),
        Players.position, Players.first_name, Players.last_name,
    ).join(Players, Players.sleeper_id == PlayerWeeklyStats.player_sleeper_id) \
     .filter(tuple_(PlayerWeeklyStats.year, PlayerWeeklyStats.week).in_(played)) \
     .group_by(PlayerWeeklyStats.player_sleeper_id, Players.position, Players.first_name, Players.last_name) \
     .order_by(func.sum(PlayerWeeklyStats.points).desc()).all()

    the_franchise_all = [
        {
            'player_sleeper_id': r.player_sleeper_id,
            'first_name': r.first_name,
            'last_name': r.last_name,
            'position': r.position,
            'total_points': round(r.total_points or 0, 1),
        }
        for r in franchise_raw
    ]

    return {
        'nuke': nuke,
        'robbed': robbed,
        'the_franchise': the_franchise_all[:5],
        'the_franchise_by_position': _by_position(the_franchise_all),
    }


@timed_cache(seconds=3600)
def get_starter_superlatives():
    """
    Starter / lineup superlatives (from PlayerWeeklyStats.is_starter):
    - workhorse: most career points scored while starting
    - tenured: most career starts (weeks in a starting lineup)
    - the_anchor: most starts with the lowest scoring average (min 10 starts)
    - bench_warmers_revenge: most career points scored while benched
    """

    played = _played_year_weeks()
    in_played = tuple_(PlayerWeeklyStats.year, PlayerWeeklyStats.week).in_(played)

    def _joined(pid, fn, ln, pos):
        return {'player_sleeper_id': pid, 'first_name': fn, 'last_name': ln, 'position': pos}

    # Workhorse — career starter points.
    workhorse_raw = db.session.query(
        PlayerWeeklyStats.player_sleeper_id,
        func.sum(PlayerWeeklyStats.points).label('total_points'),
        Players.position, Players.first_name, Players.last_name,
    ).join(Players, Players.sleeper_id == PlayerWeeklyStats.player_sleeper_id) \
     .filter(PlayerWeeklyStats.is_starter.is_(True), in_played) \
     .group_by(PlayerWeeklyStats.player_sleeper_id, Players.position, Players.first_name, Players.last_name) \
     .order_by(func.sum(PlayerWeeklyStats.points).desc()).all()

    # Tenured — most career starts.
    tenured_raw = db.session.query(
        PlayerWeeklyStats.player_sleeper_id,
        func.count().label('starts'),
        Players.position, Players.first_name, Players.last_name,
    ).join(Players, Players.sleeper_id == PlayerWeeklyStats.player_sleeper_id) \
     .filter(PlayerWeeklyStats.is_starter.is_(True), in_played) \
     .group_by(PlayerWeeklyStats.player_sleeper_id, Players.position, Players.first_name, Players.last_name) \
     .order_by(func.count().desc()).all()

    # The Anchor — lowest scoring average among the oft-started (min 10 starts).
    anchor_raw = db.session.query(
        PlayerWeeklyStats.player_sleeper_id,
        func.count().label('starts'),
        func.avg(PlayerWeeklyStats.points).label('avg_points'),
        Players.position, Players.first_name, Players.last_name,
    ).join(Players, Players.sleeper_id == PlayerWeeklyStats.player_sleeper_id) \
     .filter(PlayerWeeklyStats.is_starter.is_(True), in_played) \
     .group_by(PlayerWeeklyStats.player_sleeper_id, Players.position, Players.first_name, Players.last_name) \
     .having(func.count() >= 10) \
     .order_by(func.avg(PlayerWeeklyStats.points).asc()).all()

    # Bench Warmer's Revenge — career points scored while benched.
    bench_raw = db.session.query(
        PlayerWeeklyStats.player_sleeper_id,
        func.sum(PlayerWeeklyStats.points).label('bench_points'),
        func.count().label('games_benched'),
        Players.position, Players.first_name, Players.last_name,
    ).join(Players, Players.sleeper_id == PlayerWeeklyStats.player_sleeper_id) \
     .filter(PlayerWeeklyStats.is_starter.is_(False), in_played) \
     .group_by(PlayerWeeklyStats.player_sleeper_id, Players.position, Players.first_name, Players.last_name) \
     .order_by(func.sum(PlayerWeeklyStats.points).desc()).all()

    workhorse_all = [
        {**_joined(r.player_sleeper_id, r.first_name, r.last_name, r.position), 'total_points': round(r.total_points or 0, 1)}
        for r in workhorse_raw
    ]
    tenured_all = [
        {**_joined(r.player_sleeper_id, r.first_name, r.last_name, r.position), 'starts': r.starts}
        for r in tenured_raw
    ]
    the_anchor_all = [
        {**_joined(r.player_sleeper_id, r.first_name, r.last_name, r.position), 'starts': r.starts, 'avg_points': round(r.avg_points or 0, 1)}
        for r in anchor_raw
    ]
    bench_warmers_revenge_all = [
        {**_joined(r.player_sleeper_id, r.first_name, r.last_name, r.position), 'bench_points': round(r.bench_points or 0, 1), 'games_benched': r.games_benched}
        for r in bench_raw
    ]

    return {
        'workhorse': workhorse_all[:5],
        'workhorse_by_position': _by_position(workhorse_all),
        'tenured': tenured_all[:5],
        'tenured_by_position': _by_position(tenured_all),
        'the_anchor': the_anchor_all[:5],
        'the_anchor_by_position': _by_position(the_anchor_all),
        'bench_warmers_revenge': bench_warmers_revenge_all[:5],
        'bench_warmers_revenge_by_position': _by_position(bench_warmers_revenge_all),
    }


@timed_cache(seconds=3600)
def get_rivalry_superlatives():
    """
    Rivalry superlatives (from Matchups):
    - bad_blood: most-played pairing + head-to-head record
    - kryptonite: each team's most frequent conqueror
    - free_square: team that has allowed the most points all-time
    """
    completed = Matchups.query.filter(Matchups.completed.is_(True)).all()

    # Bad Blood — count each meeting once via the canonical (low < high) row.
    pair_stats = {}
    for m in completed:
        a, b = m.sleeper_roster_id, m.opponent_sleeper_roster_id
        if a is None or b is None or a >= b:
            continue
        st = pair_stats.setdefault((a, b), {'meetings': 0, 'low_wins': 0, 'high_wins': 0})
        st['meetings'] += 1
        if m.points_for > m.points_against:
            st['low_wins'] += 1
        elif m.points_against > m.points_for:
            st['high_wins'] += 1
    bad_blood_pairs = sorted(pair_stats.items(), key=lambda x: x[1]['meetings'], reverse=True)[:5]

    # Kryptonite — for each team, the opponent that has beaten them the most.
    nemesis = {}
    for m in completed:
        if m.points_against > m.points_for:  # this team lost to its opponent
            opps = nemesis.setdefault(m.sleeper_roster_id, {})
            opps[m.opponent_sleeper_roster_id] = opps.get(m.opponent_sleeper_roster_id, 0) + 1
    kryptonite_raw = []
    for roster, opps in nemesis.items():
        opp, losses = max(opps.items(), key=lambda x: x[1])
        kryptonite_raw.append((roster, opp, losses))
    kryptonite_raw.sort(key=lambda x: x[2], reverse=True)
    kryptonite_raw = kryptonite_raw[:5]

    # Free Square — most total points allowed.
    allowed = {}
    for m in completed:
        agg = allowed.setdefault(m.sleeper_roster_id, [0.0, 0])
        agg[0] += m.points_against or 0
        agg[1] += 1
    free_square_raw = sorted(allowed.items(), key=lambda x: x[1][0], reverse=True)[:5]

    roster_ids = set()
    for (a, b), _ in bad_blood_pairs:
        roster_ids.update([a, b])
    for r, o, _ in kryptonite_raw:
        roster_ids.update([r, o])
    for r, _ in free_square_raw:
        roster_ids.add(r)
    team_name = _team_namer(roster_ids)

    bad_blood = [{
        'team_1': team_name(a), 'team_2': team_name(b),
        'meetings': st['meetings'],
        'team_1_wins': st['low_wins'], 'team_2_wins': st['high_wins'],
    } for (a, b), st in bad_blood_pairs]

    kryptonite = [{
        'team_name': team_name(r), 'nemesis_name': team_name(o), 'losses': losses,
    } for r, o, losses in kryptonite_raw]

    free_square = [{
        'team_name': team_name(r), 'points_allowed': round(agg[0], 1), 'games': agg[1],
    } for r, agg in free_square_raw]

    return {
        'bad_blood': bad_blood,
        'kryptonite': kryptonite,
        'free_square': free_square,
    }


@timed_cache(seconds=3600)
def get_playoff_superlatives():
    """
    Playoff superlatives (from PlayoffMatchups winners brackets):
    - frequent_flyer: most playoff appearances (distinct winners-bracket years)
    - mr_january: best playoff scoring average (min 5 games), with games played

    PlayoffMatchups stores no week or points, so bracket games are mapped back to
    Matchups by team pairing (preferring the latest-week meeting, i.e. the playoff
    game) to recover each team's score — the same approach used for champion runs.
    """
    winners = PlayoffMatchups.query.filter_by(bracket='winners').all()

    # Frequent Flyer — distinct playoff years per team.
    appearances = {}
    for m in winners:
        for rid in (m.sleeper_roster_id, m.opponent_sleeper_roster_id):
            if rid is not None:
                appearances.setdefault(rid, set()).add(m.year)
    frequent_flyer_raw = sorted(appearances.items(), key=lambda x: len(x[1]), reverse=True)[:5]

    # Mr. January — playoff scoring average.
    games_by_year = {}
    for m in winners:
        games_by_year.setdefault(m.year, []).append(m)

    playoff_totals = {}
    for year, games in games_by_year.items():
        # Latest-week meeting per pairing = the playoff game (playoffs are late season).
        score_by_pair = {}
        for mt in Matchups.query.filter_by(year=year).all():
            key = (mt.sleeper_roster_id, mt.opponent_sleeper_roster_id)
            cur = score_by_pair.get(key)
            if cur is None or (mt.week or 0) > (cur.week or 0):
                score_by_pair[key] = mt
        for g in games:
            for rid, opp in ((g.sleeper_roster_id, g.opponent_sleeper_roster_id),
                             (g.opponent_sleeper_roster_id, g.sleeper_roster_id)):
                if rid is None or opp is None:
                    continue
                ms = score_by_pair.get((rid, opp))
                if not ms or not ms.completed:
                    continue
                agg = playoff_totals.setdefault(rid, [0.0, 0])
                agg[0] += ms.points_for or 0
                agg[1] += 1

    mr_january_raw = [
        (rid, total / games, games)
        for rid, (total, games) in playoff_totals.items()
        if games >= 5
    ]
    mr_january_raw.sort(key=lambda x: x[1], reverse=True)
    mr_january_raw = mr_january_raw[:5]

    roster_ids = set()
    for rid, _ in frequent_flyer_raw:
        roster_ids.add(rid)
    for rid, _, _ in mr_january_raw:
        roster_ids.add(rid)
    team_name = _team_namer(roster_ids)

    frequent_flyer = [{
        'team_name': team_name(rid),
        'appearances': len(years),
        'first_year': min(years), 'last_year': max(years),
    } for rid, years in frequent_flyer_raw]

    mr_january = [{
        'team_name': team_name(rid),
        'avg_points': round(avg, 1),
        'games': games,
    } for rid, avg, games in mr_january_raw]

    return {
        'frequent_flyer': frequent_flyer,
        'mr_january': mr_january,
    }
