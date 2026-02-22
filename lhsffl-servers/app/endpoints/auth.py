import os
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.models.users import Users
from app import db

auth = Blueprint('auth', __name__)


def _token_pair(user):
    """Return a fresh access + refresh token pair for the given user."""
    claims = {'admin': user.admin, 'team_owner': user.team_owner}
    return {
        'access_token': create_access_token(identity=str(user.user_id), additional_claims=claims),
        'refresh_token': create_refresh_token(identity=str(user.user_id)),
    }


@auth.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user = db.session.get(Users, int(get_jwt_identity()))

    if not user:
        return jsonify(error='User not found'), 404

    return jsonify(access_token=_token_pair(user)['access_token'])


@auth.route('/auth/google', methods=['POST'])
def google_login():
    data = request.get_json() or {}
    credential = data.get('credential')

    if not credential:
        return jsonify(error='Google credential required'), 400

    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    if not client_id:
        return jsonify(error='Google OAuth is not configured'), 500

    try:
        id_info = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id)
    except ValueError:
        return jsonify(error='Invalid Google token'), 401

    google_id = id_info['sub']
    email = id_info.get('email')

    # Find by google_id first, then fall back to email to link existing accounts
    user = Users.query.filter_by(google_id=google_id).first()

    if not user and email:
        user = Users.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id

    if not user:
        user = Users(
            user_name=email.split('@')[0] if email else google_id,
            first_name=id_info.get('given_name', ''),
            last_name=id_info.get('family_name', ''),
            email=email,
            google_id=google_id,
        )
        db.session.add(user)

    db.session.commit()

    return jsonify(**_token_pair(user), user=user.serialize())


@auth.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    # Tokens are stateless — the client drops them on its side.
    # A token blocklist can be added here later for immediate revocation.
    return jsonify(success=True)


@auth.route('/auth/me', methods=['GET'])
@jwt_required()
def me():
    user = db.session.get(Users, int(get_jwt_identity()))

    if not user:
        return jsonify(error='User not found'), 404

    return jsonify(user=user.serialize())
