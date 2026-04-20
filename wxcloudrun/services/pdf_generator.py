"""
PDF Generator for Battery Test Reports
Uses Pillow to render Chinese text as images, bypassing reportlab TTFont issues
"""
import os
import sys

# Alpine Linux md5 patch
import hashlib
_original_md5 = hashlib.md5
def _patched_md5(data=b'', *, usedforsecurity=True, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _original_md5(data, **kwargs)
hashlib.md5 = _patched_md5

from io import BytesIO
from datetime import datetime
import base64

_pillow_font = None
_font_cache = {}  # Cache font objects by size
_SCALE = 2  # Render at 2x resolution for crisp text

try:
    from PIL import Image, ImageDraw, ImageFont
    _pillow_available = True
    # Try to load Chinese font - store path for reuse
    _chinese_font_path = None
    _font_paths = [
        '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/noto/NotoSansCJKsc-Regular.ttc',
        '/usr/share/fonts/noto/NotoSansCJKtc-Regular.ttc',
        '/usr/share/fonts/noto/NotoSans-Regular.ttc',
        '/usr/share/fonts/noto/NotoSerifCJK-Regular.ttc',
        '/usr/share/fonts/noto/NotoSerifCJK-Bold.ttc',
    ]
    for fp in _font_paths:
        if os.path.exists(fp):
            try:
                # PIL can load TTC files - store path for later
                _chinese_font_path = fp
                print(f"DEBUG: PIL found Chinese font at {fp}", flush=True)
                break
            except Exception as e:
                print(f"DEBUG: PIL failed font {fp}: {e}", flush=True)
    if _chinese_font_path is None:
        print("DEBUG: PIL could not find any Chinese font", flush=True)
except ImportError as e:
    print(f"DEBUG: PIL not available: {e}", flush=True)
    _pillow_available = False

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

PAGE_W, PAGE_H = A4
MARGIN = 25 * mm
COL_WIDTHS = [12*mm, 50*mm, 28*mm, 32*mm, 26*mm]
HEADERS = ['序号', '应急装置安装地点', '放电时间', '剩余电量%', '备注']
TIME_POINTS = ['0分钟', '20分钟', '40分钟', '80分钟', '100分钟', '120分钟']


def _get_pil_font(size):
    """Get or create cached PIL font object for given size"""
    global _chinese_font_path
    if not _pillow_available or _chinese_font_path is None:
        return None
    # Use 2x size for crisp rendering, cache by scaled size
    scaled_size = size * _SCALE
    key = f"{_chinese_font_path}_{scaled_size}"
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(_chinese_font_path, scaled_size)
        except Exception as e:
            print(f"DEBUG: Failed to load PIL font size {scaled_size}: {e}", flush=True)
            return None
    return _font_cache[key]


def render_chinese_text(text, font_size=12, color=(0, 0, 0)):
    """Render Chinese text to a PIL image and return as bytes"""
    if not _pillow_available or _chinese_font_path is None:
        return None
    try:
        font = _get_pil_font(font_size)
        if font is None:
            return None
        # Get text size using textbbox at scaled resolution
        try:
            img_temp = Image.new('RGB', (1, 1), (255, 255, 255))
            draw_temp = ImageDraw.Draw(img_temp)
            bbox = draw_temp.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception as e:
            print(f"DEBUG: textbbox failed: {e}", flush=True)
            text_w = int(len(text) * font_size * _SCALE * 0.6)
            text_h = font_size * _SCALE
        # Create image with correct size (white background) at 2x resolution
        img = Image.new('RGBA', (text_w + 10, text_h + 4), (255, 255, 255, 255))
        draw_img = ImageDraw.Draw(img)
        draw_img.text((5, 2), text, font=font, fill=color + (255,))
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"DEBUG: render_chinese_text failed: {e}", flush=True)
        return None


def draw_chinese(c, text, x, y, font_size=12, color=(0, 0, 0)):
    """Draw Chinese text either via PIL image or fallback"""
    if _pillow_available and _chinese_font_path is not None:
        img_buf = render_chinese_text(text, font_size, color)
        if img_buf:
            try:
                img_reader = ImageReader(img_buf)
                c.drawImage(img_reader, x, y, preserveAspectRatio=True, mask='auto')
                return
            except Exception as e:
                print(f"DEBUG: drawImage failed: {e}", flush=True)
    # Fallback: just draw text (will show squares for Chinese)
    c.setFont('Helvetica', font_size)
    c.drawString(x, y, text)


def draw_chinese_centered(c, text, x, y, width, font_size=12, color=(0, 0, 0)):
    """Draw Chinese text centered within a width"""
    if _pillow_available and _chinese_font_path is not None:
        img_buf = render_chinese_text(text, font_size, color)
        if img_buf:
            try:
                img_reader = ImageReader(img_buf)
                img_w = img_reader.getSize()[0]
                # Center the image
                img_x = x + (width - img_w) / 2
                c.drawImage(img_reader, img_x, y, preserveAspectRatio=True, mask='auto')
                return
            except Exception as e:
                print(f"DEBUG: drawImage centered failed: {e}", flush=True)
    # Fallback
    c.setFont('Helvetica', font_size)
    tw = c.stringWidth(text, 'Helvetica', font_size)
    c.drawString(x + (width - tw) / 2, y, text)


class PDFGenerator:
    def generate(self, data, output_dir):
        tests = data.get('tests', [])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        loc = (tests[0].get('location', 'unknown') if tests else 'unknown')
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

        # Title - use draw_chinese_centered for full title with Chinese
        title_text = f'应急装置电池放电时间记录表  ({test_num}/{total_tests})'
        draw_chinese(c, title_text, MARGIN, y, font_size=14)
        y -= 10 * mm

        # Location info
        loc_val = test.get('location', '')
        start_time = test.get('startTime', '')
        draw_chinese(c, f'安装地点：{loc_val}　　　开始时间：{start_time}', MARGIN, y, font_size=9)
        y -= 8 * mm

        # Table headers
        x = MARGIN
        for w, h_text in zip(COL_WIDTHS, HEADERS):
            c.setFillColorRGB(0.85, 0.85, 0.85)
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
            c.rect(x, y - 8*mm, w, 8*mm, fill=1, stroke=1)
            c.setFillColorRGB(0, 0, 0)
            draw_chinese_centered(c, h_text, x, y - 8*mm + 2, w, font_size=9)
            x += w
        y -= 8 * mm

        # 6 rows of data
        records = test.get('records', [])
        for i in range(6):
            voltage = ''
            if i < len(records):
                voltage = str(records[i].get('voltage', ''))

            row_y = y - row_h
            cx = MARGIN

            # Column A: sequence number
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
            c.rect(cx, row_y, COL_WIDTHS[0], row_h)
            c.setFont('Helvetica', 8)
            s = str(i + 1)
            tw = c.stringWidth(s, 'Helvetica', 8)
            c.drawString(cx + (COL_WIDTHS[0] - tw) / 2, row_y + 2, s)
            cx += COL_WIDTHS[0]

            # Column B: location (only first row)
            c.rect(cx, row_y, COL_WIDTHS[1], row_h)
            if i == 0:
                max_ch = int(COL_WIDTHS[1] / (8 * 0.5))
                disp = loc_val[:max_ch] + ('..' if len(loc_val) > max_ch else '')
                draw_chinese(c, disp, cx + 2, row_y + 2, font_size=8)
            cx += COL_WIDTHS[1]

            # Column C: discharge time
            c.rect(cx, row_y, COL_WIDTHS[2], row_h)
            t = TIME_POINTS[i]
            draw_chinese(c, t, cx + (COL_WIDTHS[2] - c.stringWidth(t, 'Helvetica', 8)) / 2, row_y + 2, font_size=8)
            cx += COL_WIDTHS[2]

            # Column D: remaining battery
            c.rect(cx, row_y, COL_WIDTHS[3], row_h)
            c.setFont('Helvetica', 8)
            tw = c.stringWidth(voltage, 'Helvetica', 8)
            c.drawString(cx + (COL_WIDTHS[3] - tw) / 2, row_y + 2, voltage)
            cx += COL_WIDTHS[3]

            # Column E: remarks (only first row)
            c.rect(cx, row_y, COL_WIDTHS[4], row_h)
            if i == 0:
                draw_chinese(c, start_time[:15], cx + 2, row_y + 2, font_size=7)

            y = row_y

        # Photo area
        photos = [rec.get('photoBase64', '') for rec in records if rec.get('photoBase64')]
        if photos:
            y -= 6 * mm
            draw_chinese(c, '放电测试照片记录', MARGIN, y, font_size=10)
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
                px = MARGIN + col * (photo_w + gap)
                py = y - photo_h
                if photo_data and photo_data.startswith('data:image'):
                    try:
                        b64 = photo_data.split(',')[1]
                        img_bytes = base64.b64decode(b64)
                        img_buf = BytesIO(img_bytes)
                        img_reader = ImageReader(img_buf)
                        c.drawImage(img_reader, px, py, width=photo_w, height=photo_h, preserveAspectRatio=True)
                    except Exception as e:
                        print(f"DEBUG: photo error: {e}", flush=True)
                c.setStrokeColorRGB(0.5, 0.5, 0.5)
                c.rect(px, py, photo_w, photo_h)


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