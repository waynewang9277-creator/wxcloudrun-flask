from flask import Blueprint, request, jsonify, send_file
import os
import base64
import uuid

# 测试 pdf_generator 导入（在函数内部 import 避免启动时崩溃）
IMPORT_RESULT = 'not_tried'

battery_test_bp = Blueprint('battery_test', __name__)

OUTPUT_DIR = '/tmp/reports'
PHOTOS_DIR = '/tmp/reports/photos'


def get_output_dir():
    return OUTPUT_DIR


def get_photos_dir():
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    return PHOTOS_DIR


@battery_test_bp.route('/fonts', methods=['GET'])
def list_fonts():
    """Debug: list all available fonts on Alpine Linux"""
    import subprocess
    result = subprocess.run(['find', '/usr', '-name', '*.ttf', '-o', '-name', '*.ttc'], 
                          capture_output=True, text=True, timeout=30)
    return jsonify({
        'fonts': result.stdout,
        'returncode': result.returncode
    })

@battery_test_bp.route('/fonttest', methods=['GET'])
def test_font():
    """Test if font can be loaded and used for Chinese text"""
    try:
        from wxcloudrun.services.pdf_generator import FONT_NAME, FONT_FILE
        # Try to draw Chinese text with the registered font
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setFont(FONT_NAME, 12)
        # Test drawing Chinese
        test_str = '应急装置电池放电时间记录表'
        c.drawString(100, 700, test_str)
        c.save()
        buf.seek(0)
        # Check if PDF has the text (won't know if squares until viewing)
        import base64
        pdf_b64 = base64.b64encode(buf.read()).decode('utf-8')
        return jsonify({
            'font_name': FONT_NAME,
            'font_file': FONT_FILE,
            'test_string': test_str,
            'pdf_preview': pdf_b64[:200] + '...'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@battery_test_bp.route('/health', methods=['GET'])
def health():
    # Lazy import pdf_generator to verify it works
    global IMPORT_RESULT
    if IMPORT_RESULT == 'not_tried':
        try:
            from wxcloudrun.services import pdf_generator
            IMPORT_RESULT = 'success'
        except Exception as e:
            IMPORT_RESULT = f'fail: {str(e)[:50]}'
    return jsonify({'status': 'ok', 'pdf_import': IMPORT_RESULT})


@battery_test_bp.route('/submit', methods=['POST'])
def submit_battery_test():
    """提交电池测试数据并生成 PDF 报告"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        tests = data.get('tests', [])
        if not tests:
            return jsonify({'error': 'No tests provided'}), 400

        os.makedirs(get_output_dir(), exist_ok=True)

        # 保存照片文件，返回本地路径供 PDF 使用
        for test in tests:
            for record in test.get('records', []):
                photo_data = record.get('photoData', '')
                if photo_data and photo_data.startswith('data:image'):
                    # 提取 data:image/png;base64,xxxx 的 base64 部分
                    header, b64_data = photo_data.split(',', 1)
                    img_bytes = base64.b64decode(b64_data)
                    ext = 'png'
                    if 'jpeg' in header or 'jpg' in header:
                        ext = 'jpg'
                    filename = uuid.uuid4().hex + '.' + ext
                    filepath = os.path.join(get_photos_dir(), filename)
                    with open(filepath, 'wb') as f:
                        f.write(img_bytes)
                    record['photoLocalPath'] = filepath
                    # 保留 base64 供 PDF 使用
                    record['photoBase64'] = photo_data
                    # 清理 photoData 字段避免重复解码
                    record['photoData'] = ''

        # Lazy import 避免启动时崩溃
        from wxcloudrun.services.pdf_generator import PDFGenerator
        backend_data = {'tests': tests}
        pdf_gen = PDFGenerator()
        pdf_path = pdf_gen.generate(backend_data, get_output_dir())

        pdf_filename = os.path.basename(pdf_path)
        return jsonify({
            'success': True,
            'report_file': pdf_filename,
            'message': '报告生成成功'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@battery_test_bp.route('/report/<filename>', methods=['GET'])
def download_report(filename):
    """下载报告"""
    try:
        safe_name = os.path.basename(filename)
        file_path = os.path.join(get_output_dir(), safe_name)
        if not os.path.exists(file_path):
            return jsonify({'error': '报告文件不存在'}), 404
        return send_file(
            file_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=safe_name
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@battery_test_bp.route('/report', methods=['GET'])
def generate_demo_report():
    """生成演示报告"""
    try:
        os.makedirs(get_output_dir(), exist_ok=True)

        # Lazy import
        from wxcloudrun.services.pdf_generator import PDFGenerator

        demo_data = {
            'tests': [{
                'location': '1号楼配电室',
                'startTime': '2026-04-19 10:00',
                'records': [
                    {'voltage': '220'}, {'voltage': '218'}, {'voltage': '215'},
                    {'voltage': '210'}, {'voltage': '205'}, {'voltage': '200'}
                ]
            }]
        }
        pdf_gen = PDFGenerator()
        pdf_path = pdf_gen.generate(demo_data, get_output_dir())
        filename = os.path.basename(pdf_path)
        return jsonify({
            'success': True,
            'report_file': filename,
            'download_url': f'/api/battery-test/report/{filename}'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500