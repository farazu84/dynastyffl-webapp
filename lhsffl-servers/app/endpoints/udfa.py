from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.decorators import team_owner_required
from app.models.bid_budget import BidBudget
from app.models.udfa_bids import UDFABids
from app.models.bidding_window import BiddingWindow
from app.models.players import Players
from app.models.team_owners import TeamOwners
from app import db
from app.league_state_manager import get_current_year
from app.logic.udfa import get_udfa_player_pool, serialize_udfa_player

udfa = Blueprint('udfa', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_team_id():
    """Derive team_id from the authenticated user. Never trust client-supplied team_id."""
    user_id = int(get_jwt_identity())
    owner = TeamOwners.query.filter_by(user_id=user_id).first()
    return owner.team_id if owner else None


# ── Public ────────────────────────────────────────────────────────────────────

@udfa.route('/udfa/window', methods=['GET'])
def get_window():
    year = request.args.get('year', get_current_year(), type=int)
    window = BiddingWindow.query.filter_by(year=year).first()
    if not window:
        return jsonify(success=True, window=None)
    return jsonify(success=True, window=window.serialize())


# ── Team Owner ────────────────────────────────────────────────────────────────

@udfa.route('/udfa/players', methods=['GET'])
@team_owner_required
def get_udfa_players():
    year = request.args.get('year', get_current_year(), type=int)
    team_id = _get_team_id()
    if not team_id:
        return jsonify(success=False, error='No team associated with your account'), 403

    players = get_udfa_player_pool(year)

    # Index this team's bids by player — never expose other teams' bids
    my_bids = {
        b.player_sleeper_id: b.serialize()
        for b in UDFABids.query.filter_by(team_id=team_id, year=year, status='pending').all()
    }

    player_list = []
    for p in players:
        data = serialize_udfa_player(p)
        data['my_bid'] = my_bids.get(p.sleeper_id)
        player_list.append(data)

    budget = BidBudget.query.filter_by(team_id=team_id, year=year).first()

    return jsonify(success=True, players=player_list, budget=budget.serialize() if budget else None)


@udfa.route('/udfa/bids', methods=['GET'])
@team_owner_required
def get_my_bids():
    year = request.args.get('year', get_current_year(), type=int)
    team_id = _get_team_id()
    if not team_id:
        return jsonify(success=False, error='No team associated with your account'), 403

    budget = BidBudget.query.filter_by(team_id=team_id, year=year).first()
    if not budget:
        return jsonify(success=False, error='No budget found for your team this year'), 404

    bids = UDFABids.query.filter_by(team_id=team_id, year=year).all()

    sleeper_ids = [b.player_sleeper_id for b in bids]
    players_map = {
        p.sleeper_id: serialize_udfa_player(p)
        for p in Players.query.filter(Players.sleeper_id.in_(sleeper_ids)).all()
    } if sleeper_ids else {}

    bids_data = []
    for bid in bids:
        b = bid.serialize()
        b['player'] = players_map.get(bid.player_sleeper_id)
        bids_data.append(b)

    return jsonify(success=True, budget=budget.serialize(), bids=bids_data)


@udfa.route('/udfa/bids', methods=['POST'])
@team_owner_required
def place_bid():
    team_id = _get_team_id()
    if not team_id:
        return jsonify(success=False, error='No team associated with your account'), 403

    year = get_current_year()

    window = BiddingWindow.query.filter_by(year=year).first()
    if not window or not window.is_open:
        return jsonify(success=False, error='Bidding window is not open'), 400

    data = request.get_json()
    player_sleeper_id = data.get('player_sleeper_id')
    amount = data.get('amount')

    if player_sleeper_id is None:
        return jsonify(success=False, error='player_sleeper_id is required'), 400
    if not isinstance(amount, int) or amount < 1:
        return jsonify(success=False, error='Amount must be a whole dollar amount of at least $1'), 400

    # Verify this player is actually in the UDFA pool
    eligible_ids = {p.sleeper_id for p in get_udfa_player_pool(year)}
    if player_sleeper_id not in eligible_ids:
        return jsonify(success=False, error='Player is not eligible for UDFA bidding'), 400

    budget = BidBudget.query.filter_by(team_id=team_id, year=year).first()
    if not budget:
        return jsonify(success=False, error='No budget found for your team'), 404

    existing = UDFABids.query.filter_by(
        team_id=team_id, player_sleeper_id=player_sleeper_id, year=year
    ).first()

    # When updating, add back the current bid so it doesn't count against available
    current_for_player = existing.amount if existing else 0
    available = budget.starting_balance - budget.committed + current_for_player

    if amount > available:
        return jsonify(success=False, error=f'Insufficient balance. Available: ${available}'), 400

    if existing:
        existing.amount = amount
        bid = existing
    else:
        bid = UDFABids(
            bid_budget_id=budget.bid_budget_id,
            team_id=team_id,
            player_sleeper_id=player_sleeper_id,
            year=year,
            amount=amount
        )
        db.session.add(bid)

    db.session.commit()
    return jsonify(success=True, bid=bid.serialize(), budget=budget.serialize())


@udfa.route('/udfa/bids/<int:bid_id>', methods=['DELETE'])
@team_owner_required
def retract_bid(bid_id):
    team_id = _get_team_id()
    if not team_id:
        return jsonify(success=False, error='No team associated with your account'), 403

    year = get_current_year()

    window = BiddingWindow.query.filter_by(year=year).first()
    if not window or not window.is_open:
        return jsonify(success=False, error='Bidding window is not open'), 400

    bid = db.session.get(UDFABids, bid_id)
    if not bid:
        return jsonify(success=False, error='Bid not found'), 404
    if bid.team_id != team_id:
        return jsonify(success=False, error='This bid does not belong to your team'), 403
    if bid.status != 'pending':
        return jsonify(success=False, error='Can only retract pending bids'), 400

    db.session.delete(bid)
    db.session.commit()

    budget = BidBudget.query.filter_by(team_id=team_id, year=year).first()
    return jsonify(success=True, budget=budget.serialize())
