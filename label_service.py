#!/usr/bin/env python3
"""
fried-homebox-label-service
A lightweight external label service for Homebox inventory management.
Generates landscape PNG labels for Brother QL label printers.

https://github.com/friedcpu/fried-homebox-label-service
"""

import io
import logging

import qrcode
from flask import Flask, request, send_file, abort
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)

# ===========================================================================
# Configuration — edit these values
# ===========================================================================
HOMEBOX_PUBLIC_URL = "https://box.example.com"  # Prepended to relative URLs from Homebox
DOMAIN             = "box.example.com"          # Domain text shown on label
PORT               = 8099                       # Port this service listens on

# ---------------------------------------------------------------------------
# Label appearance
# ---------------------------------------------------------------------------
FONT_SIZE_TITLE  = 160  # Title font size — auto-shrinks if text is too wide
FONT_SIZE_DOMAIN = 40   # Domain font size
QR_BORDER        = 3    # White border around QR code in pixels
# ===========================================================================


def load_font(size, bold=False, oblique=False):
    if oblique:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    elif bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_label(title: str, qr_url: str, width: int, height: int) -> bytes:
    img  = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # QR code — full height minus QR_BORDER on each side
    qr_size = height - (QR_BORDER * 2)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((qr_size, qr_size), Image.NEAREST)
    img.paste(qr_img, (QR_BORDER, QR_BORDER))

    # Text area — everything to the right of the QR code
    text_area_x  = QR_BORDER + qr_size
    text_area_w  = width - text_area_x
    text_area_cx = text_area_x + text_area_w // 2

    # Auto-shrink title to fit text area width
    font_title = load_font(FONT_SIZE_TITLE, bold=True)
    for size in range(FONT_SIZE_TITLE, 20, -2):
        f    = load_font(size, bold=True)
        bbox = draw.textbbox((0, 0), title, font=f)
        if (bbox[2] - bbox[0]) <= text_area_w - 20:
            font_title = f
            break

    font_domain = load_font(FONT_SIZE_DOMAIN, oblique=True)

    # Measure text
    title_bb  = draw.textbbox((0, 0), title,  font=font_title)
    domain_bb = draw.textbbox((0, 0), DOMAIN, font=font_domain)

    title_w  = title_bb[2]  - title_bb[0]
    title_h  = title_bb[3]  - title_bb[1]
    domain_w = domain_bb[2] - domain_bb[0]
    domain_h = domain_bb[3] - domain_bb[1]

    gap     = int(height * 0.06)
    total_h = title_h + gap + domain_h
    start_y = (height - total_h) // 2

    # Title centered in text area
    draw.text(
        (text_area_cx - title_w // 2, start_y - title_bb[1]),
        title, font=font_title, fill="black"
    )

    # Domain centered in text area
    draw.text(
        (text_area_cx - domain_w // 2, start_y + title_h + gap - domain_bb[1]),
        DOMAIN, font=font_domain, fill="black"
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


@app.route("/", methods=["GET"])
def label():
    url_param   = request.args.get("URL", "")
    title_param = request.args.get("TitleText", "")
    width       = int(request.args.get("Width",  991))
    height      = int(request.args.get("Height", 306))

    log.info(f"Label request: TitleText={title_param} URL={url_param} {width}x{height}")

    if not url_param:
        abort(400, "URL parameter is required")

    # Fix relative URLs — Homebox may send /location/uuid instead of full URL
    if url_param.startswith("/"):
        url_param = HOMEBOX_PUBLIC_URL.rstrip("/") + url_param

    png_bytes = generate_label(
        title=title_param or "Unknown",
        qr_url=url_param,
        width=width,
        height=height,
    )

    return send_file(io.BytesIO(png_bytes), mimetype="image/png")


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    log.info(f"Label service running on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)
