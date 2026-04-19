from flask import Blueprint, jsonify
from .response import make_response

count_bp = Blueprint('count', __name__)

@count_bp.route('/api/count', methods=['GET'])
def get_count():
    from .model import get_count
    return make_response(data={'count': get_count()})

@count_bp.route('/api/count', methods=['POST'])
def update_count():
    from flask import request
    from .model import count_up, count_reset
    action = request.json.get('action', 'inc')
    if action == 'inc':
        count_up()
    elif action == 'clear':
        count_reset()
    return make_response(data={'count': get_count()})
