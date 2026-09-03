import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import path

from discounts.services import calculate_line_discount
from products.models import Product


@login_required
def preview_line(request):
    """Live server-side preview of price/discount for the POS screen,
    called via fetch() whenever the rep changes quantity or unit type."""
    try:
        product = Product.objects.get(pk=request.GET.get("product_id"), active=True)
    except (Product.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"error": "Product not found."}, status=404)

    unit_type = request.GET.get("unit_type", "PACK")
    try:
        quantity = int(request.GET.get("quantity", 0))
    except ValueError:
        quantity = 0

    unit_price = product.price_for(unit_type)
    gross = unit_price * quantity
    result = calculate_line_discount(unit_type, quantity, unit_price)
    discount = result["discount_amount"]
    net = gross - discount
    if net < 0:
        net = Decimal("0.00")

    return JsonResponse({
        "unit_price": str(unit_price),
        "gross_amount": str(gross),
        "discount_amount": str(discount),
        "net_amount": str(net),
        "strategy_used": result["strategy_used"],
        "current_stock": product.current_stock,
    })


urlpatterns = [
    path("sales/preview-line/", preview_line, name="preview_line"),
]
