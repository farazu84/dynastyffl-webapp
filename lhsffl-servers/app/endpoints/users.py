from flask import Blueprint, jsonify
from app.models.users import Users

users = Blueprint('users', __name__)

@users.route('/user/<int:user_id>', methods=['GET', 'OPTIONS'])
def get_user(user_id):
    user = Users.query.get(user_id)

    return jsonify(user=user.serialize(), success=True)