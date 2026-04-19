from flask import Blueprint, jsonify

# 娴嬭瘯 reportlab 鍜?pdf_generator import
try:
    from reportlab.lib.pagesizes import A4
    from wxcloudrun.services.pdf_generator import PDFGenerator
    IMPORT_OK = True
    IMPORT_ERROR = None
except Exception as e:
    IMPORT_OK = False
    IMPORT_ERROR = str(e)

battery_test_bp = Blueprint('battery_test', __name__)


@battery_test_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'reportlab': IMPORT_OK, 'error': IMPORT_ERROR})