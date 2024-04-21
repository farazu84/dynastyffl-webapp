import time
from flask import Blueprint

test = Blueprint('test', __name__)

@test.route('/ping')
def ping():
    print('here')
    return {'success': True}

@test.route('/time')
def get_current_time():
    return {'time': time.time()}