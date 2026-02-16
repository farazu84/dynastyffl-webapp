from flask import Blueprint, jsonify
from sqlalchemy.sql.expression import func
from app.models.transactions import Transactions
from app.models.transaction_players import TransactionPlayers
from app.models.transaction_rosters import TransactionRosters
from app.models.transaction_draft_picks import TransactionDraftPicks
from app.models.draft_picks import DraftPicks
from app.models.teams import Teams
from app.models.players import Players
from app import db

superlatives = Blueprint('superlatives', __name__)


@superlatives.route('/superlatives/players', methods=['GET', 'OPTIONS'])
def player_superlatives():
    """
    Player superlatives:
    - most_traded: players involved in the most trades
    - most_teams: players rostered on the most different fantasy teams
    - most_dropped: players dropped the most times
    - boomerang: players dropped then re-acquired by the same team
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

    most_traded_result = []
    for player_sleeper_id, trade_count in most_traded:
        player = Players.query.filter_by(sleeper_id=player_sleeper_id).first()
        most_traded_result.append({
            'player_sleeper_id': player_sleeper_id,
            'first_name': player.first_name if player else 'Unknown',
            'last_name': player.last_name if player else str(player_sleeper_id),
            'position': player.position if player else None,
            'trade_count': trade_count,
        })

    # Most teams rostered - count distinct roster IDs a player has been added to
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

    most_teams_result = []
    for player_sleeper_id, team_count in most_teams:
        player = Players.query.filter_by(sleeper_id=player_sleeper_id).first()
        most_teams_result.append({
            'player_sleeper_id': player_sleeper_id,
            'first_name': player.first_name if player else 'Unknown',
            'last_name': player.last_name if player else str(player_sleeper_id),
            'position': player.position if player else None,
            'team_count': team_count,
        })

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

    most_dropped_result = []
    for player_sleeper_id, drop_count in most_dropped:
        player = Players.query.filter_by(sleeper_id=player_sleeper_id).first()
        most_dropped_result.append({
            'player_sleeper_id': player_sleeper_id,
            'first_name': player.first_name if player else 'Unknown',
            'last_name': player.last_name if player else str(player_sleeper_id),
            'position': player.position if player else None,
            'drop_count': drop_count,
        })

    # Boomerang players - dropped then re-added by the same team
    # Find players who have both an 'add' and 'drop' from the same roster,
    # where the add came after the drop
    boomerang_query = db.session.query(
        TransactionPlayers.player_sleeper_id,
        TransactionPlayers.sleeper_roster_id,
        func.count().label('boomerang_count')
    ) \
        .join(Transactions) \
        .filter(TransactionPlayers.action == 'add', Transactions.status == 'complete') \
        .filter(
            db.session.query(TransactionPlayers.transaction_player_id)
            .join(Transactions, TransactionPlayers.transaction_id == Transactions.transaction_id)
            .filter(
                TransactionPlayers.player_sleeper_id == TransactionPlayers.player_sleeper_id,
                TransactionPlayers.sleeper_roster_id == TransactionPlayers.sleeper_roster_id,
                TransactionPlayers.action == 'drop',
                Transactions.status == 'complete',
            )
            .exists()
        ) \
        .group_by(TransactionPlayers.player_sleeper_id, TransactionPlayers.sleeper_roster_id) \
        .having(func.count() >= 2) \
        .order_by(func.count().desc()) \
        .limit(10) \
        .all()

    # Simpler approach: find players added to the same team multiple times
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

    boomerang_result = []
    for player_sleeper_id, roster_id, times_added in boomerang_raw:
        player = Players.query.filter_by(sleeper_id=player_sleeper_id).first()
        team = Teams.query.filter_by(sleeper_roster_id=roster_id).first()
        boomerang_result.append({
            'player_sleeper_id': player_sleeper_id,
            'first_name': player.first_name if player else 'Unknown',
            'last_name': player.last_name if player else str(player_sleeper_id),
            'position': player.position if player else None,
            'team_name': team.team_name if team else f'Roster {roster_id}',
            'times_added': times_added,
        })

    return jsonify(success=True, superlatives={
        'most_traded': most_traded_result,
        'most_teams': most_teams_result,
        'most_dropped': most_dropped_result,
        'boomerang': boomerang_result,
    })


@superlatives.route('/superlatives/teams', methods=['GET', 'OPTIONS'])
def team_superlatives():
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

    most_trades_result = []
    for roster_id, trade_count in most_trades:
        team = Teams.query.filter_by(sleeper_roster_id=roster_id).first()
        most_trades_result.append({
            'sleeper_roster_id': roster_id,
            'team_name': team.team_name if team else f'Roster {roster_id}',
            'trade_count': trade_count,
        })

    # Frequent trade partners - pairs of teams in the same trade
    # Get all trade transaction IDs with their rosters
    trade_pairs = db.session.query(
        Transactions.transaction_id,
        TransactionRosters.sleeper_roster_id
    ) \
        .join(TransactionRosters) \
        .filter(Transactions.type == 'trade', Transactions.status == 'complete') \
        .all()

    # Group rosters by transaction
    txn_rosters = {}
    for txn_id, roster_id in trade_pairs:
        txn_rosters.setdefault(txn_id, []).append(roster_id)

    # Count pairs
    pair_counts = {}
    for txn_id, rosters in txn_rosters.items():
        if len(rosters) >= 2:
            rosters_sorted = sorted(rosters)
            for i in range(len(rosters_sorted)):
                for j in range(i + 1, len(rosters_sorted)):
                    pair = (rosters_sorted[i], rosters_sorted[j])
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1

    # Sort and take top 10
    sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    trade_partners_result = []
    for (r1, r2), count in sorted_pairs:
        team1 = Teams.query.filter_by(sleeper_roster_id=r1).first()
        team2 = Teams.query.filter_by(sleeper_roster_id=r2).first()
        trade_partners_result.append({
            'team_1': team1.team_name if team1 else f'Roster {r1}',
            'team_2': team2.team_name if team2 else f'Roster {r2}',
            'trade_count': count,
        })

    # Waiver wire warriors - most waiver/FA pickups
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

    waiver_warriors_result = []
    for roster_id, pickup_count in waiver_warriors:
        team = Teams.query.filter_by(sleeper_roster_id=roster_id).first()
        waiver_warriors_result.append({
            'sleeper_roster_id': roster_id,
            'team_name': team.team_name if team else f'Roster {roster_id}',
            'pickup_count': pickup_count,
        })

    # Draft capital movers - teams that have traded the most draft picks
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

    draft_movers_result = []
    for roster_id, picks_traded in draft_movers:
        team = Teams.query.filter_by(sleeper_roster_id=roster_id).first()
        draft_movers_result.append({
            'sleeper_roster_id': roster_id,
            'team_name': team.team_name if team else f'Roster {roster_id}',
            'picks_traded': picks_traded,
        })

    return jsonify(success=True, superlatives={
        'most_trades': most_trades_result,
        'frequent_trade_partners': trade_partners_result,
        'waiver_warriors': waiver_warriors_result,
        'draft_capital_movers': draft_movers_result,
    })


@superlatives.route('/superlatives/draft', methods=['GET', 'OPTIONS'])
def draft_superlatives():
    """
    Draft superlatives:
    - startup_loyalists: players from the 2019 startup draft still on their original team
    - startup_steals: latest round startup picks still rostered in the league
    - rookie_draft_steals: lowest picked rookie draft players still on their original team
    """

    # Startup loyalists - startup draft picks still on their original drafting team
    startup_picks = DraftPicks.query.filter_by(type='startup').all()

    loyalists = []
    for pick in startup_picks:
        player = Players.query.filter_by(sleeper_id=pick.player_sleeper_id).first()
        if not player or player.team_id is None:
            continue
        team = Teams.query.get(player.team_id)
        if not team:
            continue
        # Check if the player is still on the team that drafted them
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

    # Sort by round/pick for display (earliest picks first)
    loyalists.sort(key=lambda x: x['pick_no'])

    # Startup steals - latest round startup picks still rostered anywhere
    startup_steals = []
    for pick in sorted(startup_picks, key=lambda p: -p.pick_no):
        player = Players.query.filter_by(sleeper_id=pick.player_sleeper_id).first()
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

    # Rookie draft steals - latest picked rookie draft players still on original team
    rookie_picks = DraftPicks.query \
        .filter_by(type='rookie') \
        .order_by(DraftPicks.pick_no.desc()) \
        .all()

    rookie_steals = []
    for pick in rookie_picks:
        player = Players.query.filter_by(sleeper_id=pick.player_sleeper_id).first()
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

    return jsonify(success=True, superlatives={
        'startup_loyalists': loyalists,
        'startup_steals': startup_steals,
        'rookie_draft_steals': rookie_steals,
    })
