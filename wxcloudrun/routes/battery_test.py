from flask import Blueprint, jsonify

battery_test_bp = Blueprint('battery_test', __name__)


@battery_test_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})