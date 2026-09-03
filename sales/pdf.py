"""Thermal-style receipt PDF using reportlab. No external services -
works fully offline, matches 58mm/80mm printer widths."""
import io

from django.utils import timezone
from reportlab.lib.units import mm as mm_unit
from reportlab.pdfgen import canvas


def render_receipt_pdf(sale, settings_obj):
    width_mm = settings_obj.thermal_receipt_width_mm or 80
    page_width = width_mm * mm_unit
    # generous height estimate based on number of line items
    line_count = sale.items.count()
    page_height = (90 + line_count * 8) * mm_unit

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    x_margin = 3 * mm_unit
    y = page_height - 6 * mm_unit
    line_height = 4.2 * mm_unit
    content_width = page_width - (2 * x_margin)

    def line(text, size=8, bold=False, center=False, dy=None):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        if center:
            c.drawCentredString(page_width / 2, y, text)
        else:
            c.drawString(x_margin, y, text)
        y -= dy or line_height

    def dashed():
        nonlocal y
        c.setFont("Helvetica", 8)
        c.drawString(x_margin, y, "-" * int(content_width / (3.2)))
        y -= line_height

    sym = settings_obj.currency_symbol

    line(settings_obj.company_name, size=11, bold=True, center=True)
    line(settings_obj.address, size=7.5, center=True)
    line(settings_obj.phone, size=8, center=True)
    line(settings_obj.email, size=8, center=True)
    dashed()
    line(f"Receipt: {sale.receipt_number}", size=8)
    line(f"Date: {timezone.localtime(sale.created_at):%d %b %Y, %I:%M %p} (Lagos)", size=8)
    line(f"Sold by: {sale.salesperson.get_full_name() or sale.salesperson.username}", size=8)
    if sale.customer_name:
        line(f"Customer: {sale.customer_name}", size=8)
    if sale.customer_phone:
        line(f"Phone: {sale.customer_phone}", size=8)
    dashed()

    for item in sale.items.all():
        line(f"{item.product.name}", size=8, bold=True)
        line(
            f"  {item.quantity} {item.unit_type} x {sym}{item.unit_price}  = {sym}{item.gross_amount}",
            size=7.5,
        )
        if item.discount_amount:
            line(f"  Discount: -{sym}{item.discount_amount}", size=7.5)
        line(f"  Net: {sym}{item.net_amount}", size=7.5)

    dashed()
    line(f"Subtotal: {sym}{sale.subtotal}", size=8)
    if sale.discount_total:
        line(f"Item Discount: -{sym}{sale.discount_total}", size=8)
    if sale.manual_discount_amount:
        reason = f" ({sale.manual_discount_reason})" if sale.manual_discount_reason else ""
        line(f"Extra Discount: -{sym}{sale.manual_discount_amount}{reason}", size=8)
    line(f"TOTAL: {sym}{sale.total}", size=10, bold=True)
    line(f"Payment: {sale.get_payment_method_display()}", size=8)
    line(f"Amount Paid: {sym}{sale.amount_paid}", size=8)
    if sale.balance != 0:
        label = "Change" if sale.balance >= 0 else "Balance Due"
        line(f"{label}: {sym}{abs(sale.balance)}", size=8)
    dashed()
    line(settings_obj.receipt_footer, size=7, center=True)
    line("Powered by Ice Nock Sales System", size=6, center=True)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
