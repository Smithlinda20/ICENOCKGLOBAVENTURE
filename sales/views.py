import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from audit.utils import log_action
from core.models import SystemSettings
from products.models import Product

from .models import Sale, normalize_ng_phone
from .services import SaleValidationError, cancel_sale, complete_sale


def _is_admin(user):
    return user.is_authenticated and user.is_admin_role


@login_required
def pos(request):
    products = Product.objects.filter(active=True).order_by("name")
    products_json = [
        {
            "id": p.id, "name": p.name, "sku": p.sku,
            "pack_price": str(p.pack_price), "carton_price": str(p.carton_price),
            "current_stock": p.current_stock,
        }
        for p in products
    ]
    settings_obj = SystemSettings.load()
    return render(request, "sales/pos.html", {
        "products": products,
        "products_json": products_json,
        "payment_methods": Sale.PaymentMethod.choices,
        "settings_obj": settings_obj,
    })


@login_required
def complete_sale_view(request):
    if request.method != "POST":
        return redirect("sales:pos")

    try:
        cart_items = json.loads(request.POST.get("cart_json", "[]"))
    except (json.JSONDecodeError, TypeError):
        cart_items = []

    try:
        manual_discount = Decimal(request.POST.get("manual_discount_amount") or "0")
    except InvalidOperation:
        manual_discount = Decimal("0")

    try:
        amount_paid = Decimal(request.POST.get("amount_paid") or "0")
    except InvalidOperation:
        amount_paid = Decimal("0")

    try:
        sale = complete_sale(
            salesperson=request.user,
            cart_items=cart_items,
            customer_name=request.POST.get("customer_name", "").strip(),
            customer_phone=request.POST.get("customer_phone", "").strip(),
            payment_method=request.POST.get("payment_method", Sale.PaymentMethod.CASH),
            amount_paid=amount_paid,
            manual_discount_amount=manual_discount,
            manual_discount_reason=request.POST.get("manual_discount_reason", "").strip(),
        )
    except SaleValidationError as exc:
        messages.error(request, str(exc))
        return redirect("sales:pos")

    messages.success(request, f"Sale completed. Receipt {sale.receipt_number}.")
    return redirect("sales:receipt", pk=sale.pk)


@login_required
def receipt_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related("salesperson").prefetch_related("items__product"), pk=pk)
    if not request.user.is_admin_role and sale.salesperson_id != request.user.id:
        messages.error(request, "You can only view your own receipts.")
        return redirect("sales:my_sales")
    settings_obj = SystemSettings.load()
    whatsapp_number = normalize_ng_phone(sale.customer_phone)
    whatsapp_message = build_whatsapp_message(sale, settings_obj)
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={whatsapp_message}" if whatsapp_number else ""
    return render(request, "receipts/receipt.html", {
        "sale": sale,
        "settings_obj": settings_obj,
        "whatsapp_url": whatsapp_url,
        "whatsapp_number": whatsapp_number,
        "raw_message": whatsapp_message_plain(sale, settings_obj),
    })


@login_required
def receipt_reprint(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if not request.user.is_admin_role and sale.salesperson_id != request.user.id:
        messages.error(request, "You can only reprint your own receipts.")
        return redirect("sales:my_sales")
    sale.reprint_count += 1
    sale.save(update_fields=["reprint_count"])
    log_action(request.user, "RECEIPT_REPRINT", f"Reprinted receipt {sale.receipt_number}")
    return redirect("sales:receipt", pk=sale.pk)


@login_required
def receipt_pdf(request, pk):
    from .pdf import render_receipt_pdf
    sale = get_object_or_404(Sale.objects.prefetch_related("items__product"), pk=pk)
    if not request.user.is_admin_role and sale.salesperson_id != request.user.id:
        messages.error(request, "You can only download your own receipts.")
        return redirect("sales:my_sales")
    settings_obj = SystemSettings.load()
    buffer = render_receipt_pdf(sale, settings_obj)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{sale.receipt_number}.pdf"'
    return response


@login_required
def my_sales(request):
    sales = Sale.objects.filter(salesperson=request.user).order_by("-created_at")[:200]
    return render(request, "sales/my_sales.html", {"sales": sales})


@user_passes_test(_is_admin)
def all_sales(request):
    sales = Sale.objects.select_related("salesperson").order_by("-created_at")

    receipt_no = request.GET.get("receipt", "").strip()
    product_q = request.GET.get("product", "").strip()
    rep_id = request.GET.get("salesperson", "").strip()
    unit_type = request.GET.get("unit_type", "").strip()
    payment_method = request.GET.get("payment_method", "").strip()
    phone = request.GET.get("phone", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if receipt_no:
        sales = sales.filter(receipt_number__icontains=receipt_no)
    if product_q:
        sales = sales.filter(items__product__name__icontains=product_q).distinct()
    if rep_id:
        sales = sales.filter(salesperson_id=rep_id)
    if unit_type:
        sales = sales.filter(items__unit_type=unit_type).distinct()
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    if phone:
        sales = sales.filter(customer_phone__icontains=phone)
    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)

    from accounts.models import User
    reps = User.objects.filter(role=User.Role.SALESREP)

    return render(request, "admin_dash/sales_list.html", {
        "sales": sales[:300], "reps": reps,
        "filters": request.GET,
    })


@user_passes_test(_is_admin)
def sale_cancel(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        reason = request.POST.get("reason", "")
        cancel_sale(sale, request.user, reason=reason)
        messages.success(request, f"Sale {sale.receipt_number} cancelled and stock restored.")
        return redirect("sales:all_sales")
    return render(request, "admin_dash/sale_cancel_confirm.html", {"sale": sale})


def build_whatsapp_message(sale, settings_obj):
    """URL-encoded pre-filled WhatsApp message."""
    from urllib.parse import quote
    return quote(whatsapp_message_plain(sale, settings_obj))


def whatsapp_message_plain(sale, settings_obj):
    lines = [
        f"*{settings_obj.company_name}*",
        settings_obj.address,
        f"Receipt: {sale.receipt_number}",
        f"Date: {timezone.localtime(sale.created_at):%d %b %Y, %I:%M %p}",
        "",
    ]
    for item in sale.items.all():
        lines.append(f"{item.product.name} x{item.quantity} {item.unit_type} = {settings_obj.currency_symbol}{item.net_amount}")
    lines += [
        "",
        f"Subtotal: {settings_obj.currency_symbol}{sale.subtotal}",
        f"Discount: {settings_obj.currency_symbol}{sale.discount_total + sale.manual_discount_amount}",
        f"Total: {settings_obj.currency_symbol}{sale.total}",
        f"Paid ({sale.get_payment_method_display()}): {settings_obj.currency_symbol}{sale.amount_paid}",
        "",
        settings_obj.receipt_footer,
        f"{settings_obj.phone} | {settings_obj.email}",
    ]
    return "\n".join(lines)
