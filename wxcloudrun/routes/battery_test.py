from flask import Blueprint, jsonify

# 娴嬭瘯 reportlab import
try:
    from reportlab.lib.pagesizes import A4
    REPORTLAB_OK = True
except Exception as e:
    REPORTLAB_OK = str(e)

battery_test_bp = Blueprint('battery_test', __name__)


@battery_test_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'reportlab': REPORTLAB_OK})