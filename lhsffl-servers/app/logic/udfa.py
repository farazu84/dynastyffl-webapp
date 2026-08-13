from decimal import Decimal, InvalidOperation, ROUND_DOWN

from app import db
from app.logic.money import CENT, ZERO, cents_of, format_money, to_money
from app.models.bid_budget import BidBudget
from app.models.udfa_bids import UDFABids
from app.models.bidding_window import BiddingWindow
from app.models.draft_picks import DraftPicks
from app.models.players import Players

MIN_BID = Decimal('1')


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
    """
    10% of whatever the team had left after the previous year's settlement, to the cent.

    This is where a fractional budget comes from: $105 left over carries $10.50, giving a $110.50
    budget whose $0.50 can be spent on exactly one bid (see validate_fractional_bid). Rounds down
    so carryover can never invent money the team did not have.
    """
    prev = BidBudget.query.filter_by(team_id=team_id, year=prev_year).first()
    if not prev:
        return ZERO
    prev_won = sum(
        (to_money(b.amount) for b in UDFABids.query.filter_by(
            team_id=team_id, year=prev_year, status='won'
        ).all()),
        ZERO
    )
    remaining = to_money(prev.starting_balance) - prev_won
    return (remaining / 10).quantize(CENT, rounding=ROUND_DOWN)


def parse_bid_amount(raw):
    """
    Coerce a client-supplied bid amount to a 2dp Decimal, or raise ValueError.

    Rejects anything that is not a plain number (including bool, which is an int in Python), more
    precision than cents, and amounts below the $1 minimum.
    """
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
        raise ValueError('Amount must be a dollar amount.')

    try:
        amount = Decimal(str(raw))
    except InvalidOperation:
        raise ValueError('Amount must be a dollar amount.')

    if not amount.is_finite():
        raise ValueError('Amount must be a dollar amount.')
    if amount != amount.quantize(CENT):
        raise ValueError('Amount cannot be more precise than cents.')
    if amount < MIN_BID:
        raise ValueError('Amount must be at least $1.')

    return amount.quantize(CENT)


def validate_fractional_bid(budget, amount, other_bids):
    """
    Enforce the three fractional-bid rules. Raises ValueError with a user-facing message.

    A team's budget may carry a fraction (e.g. the $0.50 of a $110.50 budget), and that fraction is
    a single indivisible unit:

      R1  You must have a fraction to use one. A whole-dollar budget permits no fractional bid.
      R2  If you use the fraction, you use the whole fraction — a fractional bid's cents must equal
          the budget's cents exactly. No partial spend, no splitting it across players.
      R3  The fraction is used once. At most one of a team's bids for the year may be fractional.

    So every legal bid is either a whole dollar amount, or a whole dollar amount plus exactly the
    budget's cents. `other_bids` must exclude the bid being edited, or editing a fractional bid in
    place would fail R3 against itself.

    Mirrored client-side in BidModal.js; this remains the authoritative check.
    """
    amount_cents = cents_of(amount)
    if amount_cents == ZERO:
        return  # Whole-dollar bids are always legal.

    budget_cents = budget.cents

    # R1 — nothing to spend.
    if budget_cents == ZERO:
        raise ValueError('Your budget has no cents to spend, so bids must be whole dollars.')

    # R2 — all of it or none of it.
    if amount_cents != budget_cents:
        raise ValueError(
            f'A fractional bid must use your full ${format_money(budget_cents)} '
            f'— ${format_money(amount_cents)} is not allowed.'
        )

    # R3 — only once.
    existing = next((b for b in other_bids if cents_of(b.amount) != ZERO), None)
    if existing:
        player = existing.player
        who = f'{player.first_name} {player.last_name}' if player else 'another player'
        raise ValueError(
            f'You have already used your ${format_money(budget_cents)} on {who}. '
            f'Retract that bid to move it.'
        )


def settle_bids(year):
    """
    Resolve all pending bids for the given year.
    Highest bid wins; ties broken by lowest waiver_order.
    Returns a list of result dicts and raises ValueError if already processed.

    Amounts are compared as 2dp Decimals so that a tie is detected exactly — the fractional bid
    rules exist precisely so a team can outbid a rival by cents, which only works if $100.50 and
    $100.50 compare equal and fall through to waiver_order.
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
        max_amount = max(to_money(b.amount) for b in bids)
        top_bids = [b for b in bids if to_money(b.amount) == max_amount]
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
            # float, matching the serialized bid/budget fields — a raw Decimal would jsonify to a
            # string and the admin results view would be the odd one out.
            'winning_amount': float(to_money(winner.amount)),
        })

    window.processed = True
    db.session.commit()

    return results
