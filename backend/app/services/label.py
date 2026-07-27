import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from app.db.models import Shipment
from app.services.delhivery import check_pincode_serviceability

PAGE_W = 4 * inch
PAGE_H = 6 * inch
MARGIN = 0.15 * inch
BOX_L = MARGIN
BOX_R = PAGE_W - MARGIN
BOX_W = BOX_R - BOX_L

LOGO_PATH = str(Path(__file__).resolve().parent.parent / "assets" / "delhivery_logo.png")


def _barcode_image(value: str) -> ImageReader:
    buf = io.BytesIO()
    barcode.Code128(value, writer=ImageWriter()).write(
        buf, options={"write_text": False, "quiet_zone": 0, "module_height": 12}
    )
    buf.seek(0)
    return ImageReader(buf)


def _wrapped_lines(text: str, font: str, size: float, max_width: float) -> List[str]:
    """Greedy word-wrap that also hard-breaks any single word wider than max_width
    (e.g. a SKU code with no spaces), so text never overflows its column."""
    lines: List[str] = []
    current = ""
    for word in (text or "").split(" "):
        if not word:
            continue
        candidate = f"{current} {word}" if current else word
        if stringWidth(candidate, font, size) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        if stringWidth(word, font, size) <= max_width:
            current = word
            continue
        chunk = ""
        for ch in word:
            piece = chunk + ch
            if stringWidth(piece, font, size) <= max_width or not chunk:
                chunk = piece
            else:
                lines.append(chunk)
                chunk = ch
        current = chunk
    if current:
        lines.append(current)
    return lines or [""]


async def build_label_pdf(shipment: Shipment) -> bytes:
    sender = shipment.sender or {}
    receiver = shipment.receiver or {}
    items = shipment.items or []
    refnum = ""
    if shipment.delhivery_response:
        packages = shipment.delhivery_response.get("packages") or []
        if packages:
            refnum = packages[0].get("refnum", "")

    pin_info = await check_pincode_serviceability(receiver.get("pincode", ""))
    raw = pin_info.get("raw_data", {})
    sort_code = raw.get("sort_code", "")
    locality = raw.get("inc", f"{receiver.get('city', '')} ({receiver.get('state', '')})")

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    y = PAGE_H - MARGIN

    def hline(y_pos: float) -> None:
        c.line(BOX_L, y_pos, BOX_R, y_pos)

    def vline(x_pos: float, y_top: float, y_bottom: float) -> None:
        c.line(x_pos, y_top, x_pos, y_bottom)

    c.setLineWidth(1.4)

    # --- Section 1: seller / delhivery header, barcode, pin / sort code ---
    top = y
    hline(top)
    mid_x = BOX_L + BOX_W * 0.45
    sender_name = sender.get("name", "")
    name_lines = _wrapped_lines(sender_name, "Helvetica-Bold", 9, mid_x - BOX_L - 2 * 4) or [""]
    header_h = max(34, len(name_lines) * 11 + 12)

    c.setFont("Helvetica-Bold", 9)
    ty = top - (header_h - len(name_lines) * 11) / 2 - 8
    for nline in name_lines:
        c.drawCentredString((BOX_L + mid_x) / 2, ty, nline)
        ty -= 11
    try:
        logo = ImageReader(LOGO_PATH)
        c.drawImage(
            logo, mid_x + 6, top - header_h / 2 - 10, width=BOX_R - mid_x - 12, height=20,
            preserveAspectRatio=True, mask="auto",
        )
    except Exception:
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString((mid_x + BOX_R) / 2, top - header_h / 2 - 4, "Delhivery")
    y = top - header_h
    vline(mid_x, top, y)
    hline(y)

    barcode_h = 55
    bc_img = _barcode_image(shipment.waybill or "")
    bc_w = BOX_W * 0.85
    c.drawImage(bc_img, BOX_L + (BOX_W - bc_w) / 2, y - barcode_h + 12, width=bc_w, height=barcode_h - 16,
                mask="auto")
    c.setFont("Courier-Bold", 9)
    c.drawCentredString(PAGE_W / 2, y - barcode_h + 4, shipment.waybill or "")
    y -= barcode_h
    hline(y)

    pin_row_h = 18
    c.setFont("Helvetica", 9)
    c.drawString(BOX_L + 4, y - pin_row_h / 2 - 3, str(receiver.get("pincode", "")))
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(BOX_R - 4, y - pin_row_h / 2 - 3, sort_code)
    y -= pin_row_h
    hline(y)

    # --- Section 2: Ship To / payment ---
    ship_col_w = BOX_W * 0.72
    ship_x = BOX_L + ship_col_w
    pad = 4
    text_w = ship_col_w - 2 * pad
    lines = [
        ("Helvetica-Bold", 8, "Ship To:"),
        ("Helvetica-Bold", 9, str(receiver.get("name", "")).upper()),
        ("Helvetica", 8, receiver.get("name", "")),
        ("Helvetica", 8, receiver.get("address", "")),
        ("Helvetica", 8, locality),
        ("Helvetica-Bold", 8, f"PIN: {receiver.get('pincode', '')}"),
    ]
    line_gap = 10
    ship_block_h = pad * 2
    wrapped: List[tuple] = []
    for font, size, text in lines:
        for wline in _wrapped_lines(text, font, size, text_w) or [""]:
            wrapped.append((font, size, wline))
            ship_block_h += line_gap

    amount = shipment.cod_amount if shipment.payment_mode == "COD" else sum(
        (i.get("price", 0) * i.get("qty", 1)) for i in items
    )
    payment_lines = [
        ("Helvetica-Bold", 9, "COD" if shipment.payment_mode == "COD" else "Pre-paid"),
        ("Helvetica-Bold", 9, "Surface"),
        ("Helvetica-Bold", 10, f"INR {amount:g}"),
    ]
    payment_block_h = len(payment_lines) * 16 + pad * 2
    ship_row_h = max(ship_block_h, payment_block_h)

    ty = y - pad - 8
    for font, size, text in wrapped:
        c.setFont(font, size)
        c.drawString(BOX_L + pad, ty, text)
        ty -= line_gap

    ty = y - (ship_row_h - payment_block_h) / 2 - 14
    for font, size, text in payment_lines:
        c.setFont(font, size)
        c.drawCentredString((ship_x + BOX_R) / 2, ty, text)
        ty -= 16

    y -= ship_row_h
    vline(ship_x, y + ship_row_h, y)
    hline(y)

    # --- Section 3: seller info, product table ---
    seller_fields = [
        ("Seller: ", sender.get("name", "")),
        ("Address: ", sender.get("address", "")),
        ("GST: ", shipment.seller_gst or ""),
    ]
    seller_wrapped: List[tuple] = []
    for label, value in seller_fields:
        label_w = c.stringWidth(label, "Helvetica-Bold", 7.5)
        chunks = _wrapped_lines(value, "Helvetica", 7.5, BOX_W - 2 * pad - label_w) or [""]
        seller_wrapped.append((label, chunks[0]))
        for chunk in chunks[1:]:
            seller_wrapped.append((None, chunk))
    info_row_h = max(len(seller_wrapped) * 10 + 8, 24)

    ty = y - 10
    for label, text in seller_wrapped:
        x = BOX_L + pad
        if label:
            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(x, ty, label)
            x += c.stringWidth(label, "Helvetica-Bold", 7.5)
        c.setFont("Helvetica", 7.5)
        c.drawString(x, ty, text)
        ty -= 10

    y -= info_row_h
    hline(y)

    header_row_h = 16
    col1_w = BOX_W * 0.55
    col2_x = BOX_L + col1_w
    col3_x = BOX_L + col1_w + (BOX_W - col1_w) / 2
    c.setFont("Helvetica-Bold", 8)
    c.drawString(BOX_L + pad, y - header_row_h / 2 - 3, "Product (Qty)")
    c.drawCentredString((col2_x + col3_x) / 2, y - header_row_h / 2 - 3, "Price")
    c.drawCentredString((col3_x + BOX_R) / 2, y - header_row_h / 2 - 3, "Total")
    y -= header_row_h
    vline(col2_x, y + header_row_h, y)
    vline(col3_x, y + header_row_h, y)
    hline(y)

    total_amount = 0.0
    for item in items:
        qty = item.get("qty", 1)
        price = item.get("price", 0)
        line_total = price * qty
        total_amount += line_total
        name_lines = _wrapped_lines(f"{item.get('name', '')} (Qty: {qty})", "Helvetica", 8, col1_w - 2 * pad) or [""]
        item_row_h = max(len(name_lines) * 10 + 6, 18)

        c.setFont("Helvetica", 8)
        ty = y - 10
        for nline in name_lines:
            c.drawString(BOX_L + pad, ty, nline)
            ty -= 10
        c.drawCentredString((col2_x + col3_x) / 2, y - item_row_h / 2 - 3, f"INR {price:g}")
        c.drawCentredString((col3_x + BOX_R) / 2, y - item_row_h / 2 - 3, f"INR {line_total:g}")
        y -= item_row_h
        vline(col2_x, y + item_row_h, y)
        vline(col3_x, y + item_row_h, y)
        hline(y)

    footer_row_h = 16
    c.setFont("Helvetica-Bold", 8)
    c.drawString(BOX_L + pad, y - footer_row_h / 2 - 3, "Total")
    c.drawCentredString((col3_x + BOX_R) / 2, y - footer_row_h / 2 - 3, f"INR {total_amount:g}")
    y -= footer_row_h
    hline(y)

    # --- Section 4: return barcode, return address ---
    ret_barcode_h = 45
    if refnum:
        ret_img = _barcode_image(refnum)
        ret_w = BOX_W * 0.6
        c.drawImage(ret_img, BOX_L + (BOX_W - ret_w) / 2, y - ret_barcode_h + 8, width=ret_w,
                    height=ret_barcode_h - 12, mask="auto")
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(PAGE_W / 2, y - ret_barcode_h + 2, refnum)
    y -= ret_barcode_h
    hline(y)

    addr_label = "Return Address: "
    addr_label_w = c.stringWidth(addr_label, "Helvetica-Bold", 8)
    addr_chunks = _wrapped_lines(sender.get("address", ""), "Helvetica", 8, BOX_W - 2 * pad - addr_label_w) or [""]
    addr_wrapped = [(addr_label, addr_chunks[0])] + [(None, chunk) for chunk in addr_chunks[1:]]
    addr_row_h = len(addr_wrapped) * 10 + 6

    ty = y - 10
    for label, text in addr_wrapped:
        x = BOX_L + pad
        if label:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x, ty, label)
            x += addr_label_w
        c.setFont("Helvetica", 8)
        c.drawString(x, ty, text)
        ty -= 10
    y -= addr_row_h
    hline(y)

    vline(BOX_L, top, y)
    vline(BOX_R, top, y)

    c.showPage()
    c.save()
    return buf.getvalue()
