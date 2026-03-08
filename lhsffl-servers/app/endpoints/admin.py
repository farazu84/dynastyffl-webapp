from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app.decorators import admin_required
from app.models.articles import Articles
from app.models.users import Users
from app.models.bid_budget import BidBudget
from app.models.bidding_window import BiddingWindow
from app.models.udfa_bids import UDFABids
from app.models.players import Players
from app.models.teams import Teams
from app import db
from app.league_state_manager import get_current_year
from app.logic.udfa import serialize_udfa_player, calculate_carryover, settle_bids

admin = Blueprint('admin', __name__)


@admin.route('/admin/articles/unpublished', methods=['GET'])
@admin_required
def get_unpublished_articles():
    articles = (Articles.query
                .filter_by(published=False)
                .order_by(Articles.creation_date.desc())
                .all())
    return jsonify(success=True, articles=[a.serialize() for a in articles])


@admin.route('/admin/articles/<int:article_id>/publish', methods=['POST'])
@admin_required
def publish_article(article_id):
    article = db.session.get(Articles, article_id)

    if not article:
        return jsonify(success=False, error='Article not found'), 404

    if article.published:
        return jsonify(success=False, error='Article is already published'), 400

    article.published = True
    db.session.commit()

    return jsonify(success=True, article=article.serialize())


@admin.route('/admin/team-owners', methods=['GET'])
@admin_required
def get_team_owners():
    owners = Users.query.filter_by(team_owner=True).order_by(Users.user_name).all()
    return jsonify(success=True, users=[u.serialize() for u in owners])


@admin.route('/admin/impersonate/<int:user_id>', methods=['POST'])
@admin_required
def impersonate(user_id):
    target = db.session.get(Users, user_id)

    if not target:
        return jsonify(success=False, error='User not found'), 404

    if not target.team_owner:
        return jsonify(success=False, error='User is not a team owner'), 400

    claims = {
        'admin': target.admin,
        'team_owner': target.team_owner,
        'impersonated_by': int(get_jwt_identity()),
    }
    token = create_access_token(identity=str(target.user_id), additional_claims=claims)

    return jsonify(success=True, access_token=token, user=target.serialize())


# ── UDFA Admin ────────────────────────────────────────────────────────────────

@admin.route('/admin/udfa/window', methods=['POST'])
@admin_required
def set_udfa_window():
    data = request.get_json()
    year = data.get('year')
    opens_at = data.get('opens_at')
    closes_at = data.get('closes_at')

    if not all([year, opens_at, closes_at]):
        return jsonify(success=False, error='year, opens_at, and closes_at are required'), 400

    try:
        opens_dt = datetime.fromisoformat(opens_at)
        closes_dt = datetime.fromisoformat(closes_at)
    except ValueError:
        return jsonify(success=False, error='Invalid datetime format. Use ISO 8601.'), 400

    window = BiddingWindow.query.filter_by(year=year).first()
    if window:
        window.opens_at = opens_dt
        window.closes_at = closes_dt
    else:
        window = BiddingWindow(year=year, opens_at=opens_dt, closes_at=closes_dt)
        db.session.add(window)

    db.session.commit()
    return jsonify(success=True, window=window.serialize())


@admin.route('/admin/udfa/bids', methods=['GET'])
@admin_required
def get_all_udfa_bids():
    year = request.args.get('year', get_current_year(), type=int)

    bids = UDFABids.query.filter_by(year=year).order_by(
        UDFABids.player_sleeper_id, UDFABids.amount.desc()
    ).all()

    sleeper_ids = list({b.player_sleeper_id for b in bids})
    players_map = {
        p.sleeper_id: serialize_udfa_player(p)
        for p in Players.query.filter(Players.sleeper_id.in_(sleeper_ids)).all()
    } if sleeper_ids else {}

    budgets = {
        b.team_id: b.serialize()
        for b in BidBudget.query.filter_by(year=year).all()
    }

    bids_data = []
    for bid in bids:
        b = bid.serialize()
        b['player'] = players_map.get(bid.player_sleeper_id)
        b['team_name'] = bid.team.team_name
        b['waiver_order'] = budgets.get(bid.team_id, {}).get('waiver_order')
        bids_data.append(b)

    return jsonify(success=True, bids=bids_data, budgets=list(budgets.values()))


@admin.route('/admin/udfa/budgets', methods=['POST'])
@admin_required
def seed_udfa_budgets():
    data = request.get_json()
    year = data.get('year')
    waiver_orders = data.get('waiver_orders', {})  # {"team_id": order}

    if not year:
        return jsonify(success=False, error='year is required'), 400

    prev_year = year - 1
    prev_budgets = {b.team_id: b for b in BidBudget.query.filter_by(year=prev_year).all()}

    teams = Teams.query.all()
    created = []
    for team in teams:
        if BidBudget.query.filter_by(team_id=team.team_id, year=year).first():
            continue

        carryover = calculate_carryover(team.team_id, prev_year)
        order = int(waiver_orders.get(str(team.team_id), waiver_orders.get(team.team_id, 0)))
        budget = BidBudget(
            team_id=team.team_id,
            year=year,
            starting_balance=100 + carryover,
            waiver_order=order
        )
        db.session.add(budget)
        created.append(budget)

    db.session.commit()
    return jsonify(success=True, budgets=[b.serialize() for b in created])


@admin.route('/admin/udfa/process', methods=['POST'])
@admin_required
def process_udfa_bids():
    data = request.get_json()
    year = data.get('year', get_current_year())

    try:
        results = settle_bids(year)
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400

    return jsonify(success=True, results=results)
