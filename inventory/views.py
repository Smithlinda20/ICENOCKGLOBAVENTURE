from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render

from audit.utils import log_action
from products.models import Product
from .forms import StockAdjustmentForm
from .models import StockMovement
from .services import record_movement


def _is_admin(user):
    return user.is_authenticated and user.is_admin_role


@user_passes_test(_is_admin)
def stock_overview(request):
    products = Product.objects.all().order_by("name")
    low_stock = [p for p in products if p.is_low_stock and p.active]
    return render(request, "admin_dash/inventory_overview.html", {"products": products, "low_stock": low_stock})


@user_passes_test(_is_admin)
def stock_adjust(request):
    if request.method == "POST":
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data["product"]
            movement_type = form.cleaned_data["movement_type"]
            qty = form.cleaned_data["quantity"]
            reason = form.cleaned_data["reason"]
            signed_qty = qty if movement_type == "IN" else qty  # adjustment sign is user-supplied directly
            try:
                record_movement(product, movement_type, signed_qty, user=request.user, reason=reason)
                log_action(request.user, "STOCK_ADJUSTMENT", f"{movement_type} {signed_qty} on {product.name}: {reason}")
                messages.success(request, f"Stock updated for {product.name}.")
                return redirect("inventory:overview")
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = StockAdjustmentForm()
    return render(request, "admin_dash/stock_adjust_form.html", {"form": form})


@user_passes_test(_is_admin)
def stock_history(request):
    q = request.GET.get("product", "")
    movements = StockMovement.objects.select_related("product", "user").all()
    if q:
        movements = movements.filter(product_id=q)
    products = Product.objects.all().order_by("name")
    return render(request, "admin_dash/stock_history.html", {
        "movements": movements[:300], "products": products, "selected": q,
    })
