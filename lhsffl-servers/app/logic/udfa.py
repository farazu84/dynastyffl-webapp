from app import db
from app.models.bid_budget import BidBudget
from app.models.udfa_bids import UDFABids
from app.models.bidding_window import BiddingWindow
from app.models.draft_picks import DraftPicks
from app.models.players import Players


def serialize_udfa_player(player):
    return {
        'player_id': player.player_id,
        'sleeper_id': player.sleeper_id,
        'first_name': player.first_name,
        'last_name': player.last_name,
        'position': player.position,
        'nfl_team': player.nfl_team,
        'age': player.age,
        'college': player.college,
        'years_exp': player.years_exp,
    }


def get_udfa_player_pool(year):
    """Rookies in Sleeper who were not drafted in our rookie draft that year."""
    drafted_ids = db.session.query(DraftPicks.player_sleeper_id).filter(
        DraftPicks.type == 'rookie',
        DraftPicks.season == year
    )
    return Players.query.filter(
        Players.years_exp == 0,
        Players.team_id.is_(None),
        ~Players.sleeper_id.in_(drafted_ids)
    ).order_by(Players.position, Players.last_name).all()


def calculate_carryover(team_id, prev_year):
    """Floor of 10% of whatever the team had left after the previous year's settlement."""
    prev = BidBudget.query.filter_by(team_id=team_id, year=prev_year).first()
    if not prev:
        return 0
    prev_won = sum(
        b.amount for b in UDFABids.query.filter_by(
            team_id=team_id, year=prev_year, status='won'
        ).all()
    )
    return (prev.starting_balance - prev_won) // 10


def settle_bids(year):
    """
    Resolve all pending bids for the given year.
    Highest bid wins; ties broken by lowest waiver_order.
    Returns a list of result dicts and raises ValueError if already processed.
    """
    window = BiddingWindow.query.filter_by(year=year).first()
    if not window:
        raise ValueError(f'No bidding window found for {year}')
    if window.processed:
        raise ValueError(f'Bids already processed for {year}')

    pending = UDFABids.query.filter_by(year=year, status='pending').all()

    player_bids = {}
    for bid in pending:
        player_bids.setdefault(bid.player_sleeper_id, []).append(bid)

    results = []
    for player_sleeper_id, bids in player_bids.items():
        max_amount = max(b.amount for b in bids)
        top_bids = [b for b in bids if b.amount == max_amount]
        winner = (
            top_bids[0] if len(top_bids) == 1
            else min(top_bids, key=lambda b: b.budget.waiver_order)
        )

        winner.status = 'won'
        for bid in bids:
            if bid.bid_id != winner.bid_id:
                bid.status = 'lost'

        results.append({
            'player_sleeper_id': player_sleeper_id,
            'winner_team_id': winner.team_id,
            'winner_team_name': winner.team.team_name,
            'winning_amount': winner.amount,
        })

    window.processed = True
    db.session.commit()

    return results
