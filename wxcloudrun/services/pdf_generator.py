import os
from datetime import datetime
from io import BytesIO
import base64
import hashlib

# Alpine Linux 兼容：移除 usedforsecurity 参数
_original_md5 = hashlib.md5
def _patched_md5(data=b'', *, usedforsecurity=True, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _original_md5(data, **kwargs)
hashlib.md5 = _patched_md5

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# Debug: list all fonts in Alpine Linux
def _debug_fonts():
    font_dirs = ['/usr/share/fonts', '/usr/local/share/fonts', '/share/fonts']
    found = []
    for d in font_dirs:
        if os.path.exists(d):
            for root, dirs, files in os.walk(d):
                for f in files:
                    if any(ext in f.lower() for ext in ['.ttf', '.ttc', '.otf']):
                        found.append(os.path.join(root, f))
    return found

FONT_FILE = 'C:/Windows/Fonts/simsun.ttc'
FONT_NAME = 'Helvetica'

# Try Windows font first
try:
    pdfmetrics.registerFont(TTFont('SimSun', FONT_FILE))
    FONT_NAME = 'SimSun'
except:
    pass

# Try Alpine Linux font paths
_alpine_font_paths = [
    '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/noto/NotoSansCJKsc-Regular.ttc',
    '/usr/share/fonts/noto/NotoSansCJKtc-Regular.ttc',
    '/usr/share/fonts/noto/NotoSans-Regular.ttc',
    '/usr/share/fonts/noto/NotoSerifCJK-Regular.ttc',
    '/usr/share/fonts/noto/NotoSerifCJK-Bold.ttc',
]
# Try glob patterns too
for pattern in ['/usr/share/fonts/**/NotoSans*.ttc', '/usr/share/fonts/**/NotoSans*.ttf']:
    import glob
    for fp in glob.glob(pattern, recursive=True):
        _alpine_font_paths.append(fp)

for fp in _alpine_font_paths:
    if os.path.exists(fp):
        try:
            pdfmetrics.registerFont(TTFont('NotoSans', fp))
            FONT_NAME = 'NotoSans'
            print(f"DEBUG: Loaded font from {fp}")
            break
        except Exception as e:
            print(f"DEBUG: Failed to load font from {fp}: {e}")

PAGE_W, PAGE_H = A4
MARGIN = 25 * mm
COL_WIDTHS = [12*mm, 50*mm, 28*mm, 32*mm, 26*mm]
HEADERS = ['序号', '应急装置安装地点', '放电时间', '剩余电量%', '备注']
TIME_POINTS = ['0分钟', '20分钟', '40分钟', '80分钟', '100分钟', '120分钟']


def decode_base64_image(data: str):
    if not data:
        return None
    try:
        if ',' in data:
            data = data.split(',', 1)[1]
        img_bytes = base64.b64decode(data)
        buf = BytesIO(img_bytes)
        return ImageReader(buf)
    except Exception:
        return None


class PDFGenerator:
    def generate(self, data, output_dir):
        tests = data.get('tests', [])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        loc = (tests[0].get('location', 'unknown') if tests else 'unknown')
        # 只移除非法文件名字符，保留中文和空格
        import re
        safe_chars = re.sub(r'[/\\:*?"<>|]', '_', loc)
        loc_clean = safe_chars.strip().replace(' ', '_')
        filename = f'battery_test_report_{loc_clean}_{timestamp}.pdf'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)

        for idx, test in enumerate(tests):
            if idx > 0:
                c.showPage()
            self._draw_test_page(c, test, idx + 1, len(tests))

        c.save()
        buf.seek(0)
        with open(output_path, 'wb') as f:
            f.write(buf.read())
        return output_path

    def _draw_test_page(self, c, test, test_num, total_tests):
        row_h = 8 * mm
        y = PAGE_H - MARGIN

        # 每页标题（含测试组编号）
        c.setFont(FONT_NAME, 14)
        title = f'应急装置电池放电时间记录表  ({test_num}/{total_tests})'
        title_w = c.stringWidth(title, FONT_NAME, 14)
        c.drawString((PAGE_W - title_w) / 2, y, title)
        y -= 10 * mm

        # 地点信息行
        loc_val = test.get('location', '')
        start_time = test.get('startTime', '')
        c.setFont(FONT_NAME, 9)
        info_line = f'安装地点：{loc_val}　　　开始时间：{start_time}'
        c.drawString(MARGIN, y, info_line)
        y -= 8 * mm

        # 表头
        x = MARGIN
        for w, h_text in zip(COL_WIDTHS, HEADERS):
            c.setFillColorRGB(0.85, 0.85, 0.85)
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
            c.rect(x, y - 8*mm, w, 8*mm, fill=1, stroke=1)
            c.setFillColorRGB(0, 0, 0)
            c.setFont(FONT_NAME, 9)
            tw = c.stringWidth(h_text, FONT_NAME, 9)
            c.drawString(x + (w - tw) / 2, y - 8*mm + 2, h_text)
            x += w
        y -= 8 * mm

        # 6行数据
        records = test.get('records', [])
        for i in range(6):
            voltage = ''
            if i < len(records):
                voltage = str(records[i].get('voltage', ''))

            row_y = y - row_h
            cx = MARGIN

            # A 序号
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
            c.rect(cx, row_y, COL_WIDTHS[0], row_h)
            c.setFont(FONT_NAME, 8)
            s = str(i + 1)
            tw = c.stringWidth(s, FONT_NAME, 8)
            c.drawString(cx + (COL_WIDTHS[0] - tw) / 2, row_y + 2, s)
            cx += COL_WIDTHS[0]

            # B 地点（只在首行显示）
            c.rect(cx, row_y, COL_WIDTHS[1], row_h)
            if i == 0:
                c.setFont(FONT_NAME, 8)
                max_ch = int(COL_WIDTHS[1] / (8 * 0.5))
                disp = loc_val[:max_ch] + ('..' if len(loc_val) > max_ch else '')
                c.drawString(cx + 2, row_y + 2, disp)
            cx += COL_WIDTHS[1]

            # C 放电时间
            c.rect(cx, row_y, COL_WIDTHS[2], row_h)
            c.setFont(FONT_NAME, 8)
            t = TIME_POINTS[i]
            tw = c.stringWidth(t, FONT_NAME, 8)
            c.drawString(cx + (COL_WIDTHS[2] - tw) / 2, row_y + 2, t)
            cx += COL_WIDTHS[2]

            # D 剩余电量
            c.rect(cx, row_y, COL_WIDTHS[3], row_h)
            c.setFont(FONT_NAME, 8)
            tw = c.stringWidth(voltage, FONT_NAME, 8)
            c.drawString(cx + (COL_WIDTHS[3] - tw) / 2, row_y + 2, voltage)
            cx += COL_WIDTHS[3]

            # E 备注（只在首行显示开始时间）
            c.rect(cx, row_y, COL_WIDTHS[4], row_h)
            if i == 0:
                c.setFont(FONT_NAME, 7)
                c.drawString(cx + 2, row_y + 2, start_time[:15])

            y = row_y

        # ===== 照片区域（每个测试单独整理）=====
        photos = [rec.get('photoBase64', '') for rec in records if rec.get('photoBase64')]
        if photos:
            y -= 6 * mm
            c.setFont(FONT_NAME, 10)
            c.drawString(MARGIN, y, '放电测试照片记录')
            y -= 5 * mm

            photos_per_row = 3
            photo_area_w = PAGE_W - 2 * MARGIN
            photo_w = (photo_area_w - 4 * mm) / photos_per_row
            photo_h = photo_w * 0.75
            gap = 4 * mm

            for idx, photo_data in enumerate(photos):
                row = idx // photos_per_row
                col = idx % photos_per_row
                if y - photo_h < MARGIN + 5*mm:
                    c.showPage()
                    y = PAGE_H - MARGIN
                    c.setFont(FONT_NAME, 10)
                    c.drawString(MARGIN, y, f'放电测试照片记录（{test_num}/{total_tests} 续）')
                    y -= 5 * mm

                img_reader = decode_base64_image(photo_data)
                px = MARGIN + col * (photo_w + gap)
                py = y - photo_h
                if img_reader:
                    try:
                        c.drawImage(img_reader, px, py, width=photo_w, height=photo_h,
                                    preserveAspectRatio=True, anchor='c')
                    except Exception:
                        c.setStrokeColorRGB(0.7, 0.7, 0.7)
                        c.rect(px, py, photo_w, photo_h)
                else:
                    c.setStrokeColorRGB(0.7, 0.7, 0.7)
                    c.rect(px, py, photo_w, photo_h)

                c.setFont(FONT_NAME, 7)
                c.setFillColorRGB(0.4, 0.4, 0.4)
                label = f"照片 {idx + 1}"
                c.drawString(px, py - 3*mm, label)
                c.setFillColorRGB(0, 0, 0)

                if col == photos_per_row - 1:
                    y -= (photo_h + 4 * mm)
            else:
                if col < photos_per_row - 1:
                    y -= (photo_h + 4 * mm)

        # 页脚
        c.setFont(FONT_NAME, 7)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        footer = f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}　　第 {test_num} 页 / 共 {total_tests} 页'
        fw = c.stringWidth(footer, FONT_NAME, 7)
        c.drawString(PAGE_W - MARGIN - fw, MARGIN - 3*mm, footer)
        c.setFillColorRGB(0, 0, 0)
