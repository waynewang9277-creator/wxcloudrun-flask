from flask import Blueprint, jsonify

# 鍗曠嫭娴嬭瘯 wxcloudrun.services.pdf_generator 鐨勫鍏?IMPORT_RESULT = 'not_tried'
try:
    from wxcloudrun.services import pdf_generator
    IMPORT_RESULT = 'success'
except Exception as e:
    IMPORT_RESULT = f'fail: {str(e)[:50]}'

battery_test_bp = Blueprint('battery_test', __name__)


@battery_test_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'pdf_import': IMPORT_RESULT})