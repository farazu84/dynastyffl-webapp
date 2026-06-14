from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def team_owner_required(fn):
    """Restrict an endpoint to users with the team_owner flag set."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method == 'OPTIONS':  # let CORS preflight through (flask-cors adds headers)
            return ('', 200)
        verify_jwt_in_request()
        if not get_jwt().get('team_owner'):
            return jsonify(error='Team owner access required'), 403
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Restrict an endpoint to users with the admin flag set."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method == 'OPTIONS':  # let CORS preflight through (flask-cors adds headers)
            return ('', 200)
        verify_jwt_in_request()
        if not get_jwt().get('admin'):
            return jsonify(error='Admin access required'), 403
        return fn(*args, **kwargs)
    return wrapper
