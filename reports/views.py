import csv
import datetime

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, F, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User
from inventory.models import StockMovement
from products.models import Product
from sales.models import Sale, SaleItem


def _is_admin(user):
    return user.is_authenticated and user.is_admin_role


def _parse_range(request):
    today = timezone.localdate()
    default_from = today.replace(day=1)
    date_from = request.GET.get("date_from") or default_from.isoformat()
    date_to = request.GET.get("date_to") or today.isoformat()
    try:
        d_from = datetime.date.fromisoformat(date_from)
        d_to = datetime.date.fromisoformat(date_to)
    except ValueError:
        d_from, d_to = default_from, today
    return d_from, d_to


@user_passes_test(_is_admin)
def monthly_analysis(request):
    d_from, d_to = _parse_range(request)
    sales = Sale.objects.filter(created_at__date__gte=d_from, created_at__date__lte=d_to,
                                 status=Sale.Status.COMPLETED)
    items = SaleItem.objects.filter(sale__in=sales)

    sales_agg = sales.aggregate(
        transactions=Count("id"), gross=Sum("subtotal"),
        discounts=Sum(F("discount_total") + F("manual_discount_amount")), net=Sum("total"),
    )
    qty_sold = items.aggregate(qty=Sum("quantity"))["qty"] or 0

    by_product = (
        items.values("product__name")
        .annotate(qty=Sum("quantity"), net=Sum("net_amount"))
        .order_by("-net")[:15]
    )
    by_unit = items.values("unit_type").annotate(qty=Sum("quantity"), net=Sum("net_amount"))
    by_salesperson = (
        sales.values("salesperson__username", "salesperson__first_name", "salesperson__last_name")
        .annotate(transactions=Count("id"), net=Sum("total"))
        .order_by("-net")
    )
    by_payment = sales.values("payment_method").annotate(count=Count("id"), total=Sum("total"))

    stock_in = StockMovement.objects.filter(
        created_at__date__gte=d_from, created_at__date__lte=d_to, movement_type=StockMovement.MovementType.IN
    ).aggregate(qty=Sum("quantity"))["qty"] or 0
    returns = StockMovement.objects.filter(
        created_at__date__gte=d_from, created_at__date__lte=d_to, movement_type=StockMovement.MovementType.RETURN
    ).aggregate(qty=Sum("quantity"))["qty"] or 0

    context = {
        "date_from": d_from, "date_to": d_to,
        "sales_agg": sales_agg, "qty_sold": qty_sold,
        "by_product": by_product, "by_unit": by_unit,
        "by_salesperson": by_salesperson, "by_payment": by_payment,
        "stock_in": stock_in, "returns": returns,
        "current_stock_total": sum(p.current_stock for p in Product.objects.all()),
        "avg_transaction": (sales_agg["net"] / sales_agg["transactions"]) if sales_agg["transactions"] else 0,
    }
    return render(request, "admin_dash/reports_monthly.html", context)


@user_passes_test(_is_admin)
def salesperson_performance(request):
    d_from, d_to = _parse_range(request)
    reps = User.objects.filter(role=User.Role.SALESREP)
    rows = []
    for rep in reps:
        sales = Sale.objects.filter(salesperson=rep, created_at__date__gte=d_from,
                                     created_at__date__lte=d_to, status=Sale.Status.COMPLETED)
        agg = sales.aggregate(transactions=Count("id"), net=Sum("total"))
        rows.append({
            "rep": rep,
            "transactions": agg["transactions"] or 0,
            "net": agg["net"] or 0,
        })
    rows.sort(key=lambda r: r["net"], reverse=True)
    return render(request, "admin_dash/reports_performance.html", {"rows": rows, "date_from": d_from, "date_to": d_to})


@user_passes_test(_is_admin)
def inventory_report(request):
    products = Product.objects.all().order_by("name")
    return render(request, "admin_dash/reports_inventory.html", {"products": products})


@user_passes_test(_is_admin)
def export_sales_csv(request):
    d_from, d_to = _parse_range(request)
    sales = Sale.objects.filter(created_at__date__gte=d_from, created_at__date__lte=d_to).select_related("salesperson")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="sales_{d_from}_to_{d_to}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Receipt No", "Date", "Salesperson", "Customer", "Phone", "Payment Method",
                      "Subtotal", "Discount", "Total", "Amount Paid", "Status"])
    for s in sales:
        writer.writerow([
            s.receipt_number, timezone.localtime(s.created_at).strftime("%Y-%m-%d %H:%M"),
            s.salesperson.username, s.customer_name, s.customer_phone, s.get_payment_method_display(),
            s.subtotal, s.discount_total + s.manual_discount_amount, s.total, s.amount_paid, s.status,
        ])
    return response


@user_passes_test(_is_admin)
def export_inventory_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="inventory.csv"'
    writer = csv.writer(response)
    writer.writerow(["SKU", "Product", "Category", "Current Stock", "Minimum Stock", "Pack Price", "Carton Price", "Status"])
    for p in Product.objects.all():
        writer.writerow([p.sku, p.name, p.category, p.current_stock, p.minimum_stock,
                          p.pack_price, p.carton_price, "LOW STOCK" if p.is_low_stock else "OK"])
    return response
