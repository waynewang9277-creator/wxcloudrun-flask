from flask import Blueprint, jsonify

count_bp = Blueprint('count', __name__)


def make_json_response(data):
    return jsonify({'code': 0, 'data': data, 'msg': 'success'})


@count_bp.route('/api/count', methods=['GET'])
def get_count():
    from .model import get_count
    return make_json_response({'count': get_count()})


@count_bp.route('/api/count', methods=['POST'])
def update_count():
    from flask import request
    from .model import count_up, count_reset
    action = request.json.get('action', 'inc')
    if action == 'inc':
        count_up()
    elif action == 'clear':
        count_reset()
    return make_json_response({'count': get_count()})