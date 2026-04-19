from flask import Blueprint, request, jsonify, send_file
import os
import base64
import uuid
from .services.pdf_generator import PDFGenerator

battery_test_bp = Blueprint('battery_test', __name__)

OUTPUT_DIR = '/tmp/reports'


@battery_test_bp.route('/submit', methods=['POST'])
def submit_battery_test():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        tests = data.get('tests', [])
        if not tests:
            return jsonify({'error': 'No tests provided'}), 400
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        for test in tests:
            for record in test.get('records', []):
                photo_data = record.get('photoData', '')
                if photo_data and photo_data.startswith('data:image'):
                    header, b64_data = photo_data.split(',', 1)
                    img_bytes = base64.b64decode(b64_data)
                    ext = 'png' if not ('jpeg' in header or 'jpg' in header) else 'jpg'
                    filename = f'/tmp/{uuid.uuid4().hex}.{ext}'
                    with open(filename, 'wb') as f:
                        f.write(img_bytes)
                    record['photoLocalPath'] = filename

        backend_data = {'tests': tests}
        pdf_gen = PDFGenerator()
        pdf_path = pdf_gen.generate(backend_data, OUTPUT_DIR)
        pdf_filename = os.path.basename(pdf_path)
        return jsonify({'success': True, 'report_file': pdf_filename, 'message': '报告生成成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@battery_test_bp.route('/report/<filename>', methods=['GET'])
def download_report(filename):
    try:
        safe_name = os.path.basename(filename)
        file_path = os.path.join(OUTPUT_DIR, safe_name)
        if not os.path.exists(file_path):
            return jsonify({'error': '报告文件不存在'}), 404
        return send_file(file_path, mimetype='application/pdf', as_attachment=True, download_name=safe_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@battery_test_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'battery_test'})
