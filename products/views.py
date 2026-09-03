from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from audit.utils import log_action
from .forms import ProductForm
from .models import PriceHistory, Product


def _is_admin(user):
    return user.is_authenticated and user.is_admin_role


@login_required
def product_search_api(request):
    """Used by the POS screen for live product search (JSON)."""
    from django.http import JsonResponse

    q = request.GET.get("q", "").strip()
    qs = Product.objects.filter(active=True)
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(sku__icontains=q)
    qs = qs.order_by("name")[:25]
    data = [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "pack_price": str(p.pack_price),
            "carton_price": str(p.carton_price),
            "current_stock": p.current_stock,
            "packs_per_carton": p.packs_per_carton,
        }
        for p in qs
    ]
    return JsonResponse({"results": data})


@user_passes_test(_is_admin)
def product_list(request):
    q = request.GET.get("q", "").strip()
    qs = Product.objects.all()
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(sku__icontains=q) | qs.filter(category__icontains=q)
    return render(request, "admin_dash/products_list.html", {"products": qs.order_by("name"), "q": q})


@user_passes_test(_is_admin)
def product_edit(request, pk=None):
    instance = get_object_or_404(Product, pk=pk) if pk else None
    old_pack = instance.pack_price if instance else None
    old_carton = instance.carton_price if instance else None

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            product = form.save()
            if old_pack is not None and old_pack != product.pack_price:
                PriceHistory.objects.create(
                    product=product, field_changed=PriceHistory.Field.PACK_PRICE,
                    old_price=old_pack, new_price=product.pack_price, changed_by=request.user,
                )
            if old_carton is not None and old_carton != product.carton_price:
                PriceHistory.objects.create(
                    product=product, field_changed=PriceHistory.Field.CARTON_PRICE,
                    old_price=old_carton, new_price=product.carton_price, changed_by=request.user,
                )
            if instance is None:
                PriceHistory.objects.create(
                    product=product, field_changed=PriceHistory.Field.PACK_PRICE,
                    old_price=None, new_price=product.pack_price, changed_by=request.user,
                )
                PriceHistory.objects.create(
                    product=product, field_changed=PriceHistory.Field.CARTON_PRICE,
                    old_price=None, new_price=product.carton_price, changed_by=request.user,
                )
            log_action(request.user, "PRODUCT_CHANGE", f"Saved product {product.name} ({product.sku})")
            messages.success(request, f"Product '{product.name}' saved.")
            return redirect("products:list")
    else:
        form = ProductForm(instance=instance)
    return render(request, "admin_dash/product_form.html", {"form": form, "instance": instance})


@user_passes_test(_is_admin)
def product_price_history(request, pk):
    product = get_object_or_404(Product, pk=pk)
    history = product.price_history.select_related("changed_by")
    return render(request, "admin_dash/product_price_history.html", {"product": product, "history": history})


@user_passes_test(_is_admin)
def product_toggle_active(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.active = not product.active
    product.save(update_fields=["active"])
    log_action(request.user, "PRODUCT_CHANGE", f"{'Activated' if product.active else 'Deactivated'} {product.name}")
    messages.success(request, f"Product '{product.name}' {'activated' if product.active else 'deactivated'}.")
    return redirect("products:list")
