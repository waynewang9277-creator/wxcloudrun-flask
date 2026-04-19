from flask import Blueprint, jsonify

count_bp = Blueprint('count', __name__)


def make_json_response(data):
    return jsonify({'code': 0, 'data': data, 'msg': 'success'})


@count_bp.route('/api/count', methods=['GET'])
def get_count():
    return make_json_response({'count': 0})


@count_bp.route('/api/count', methods=['POST'])
def update_count():
    return make_json_response({'count': 0})