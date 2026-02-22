from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def admin_required(fn):
    """Restrict an endpoint to users with the admin flag set."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if not get_jwt().get('admin'):
            return jsonify(error='Admin access required'), 403
        return fn(*args, **kwargs)
    return wrapper
