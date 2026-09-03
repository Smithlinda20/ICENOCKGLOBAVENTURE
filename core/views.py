from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from audit.utils import log_action
from products.models import Product
from sales.models import Sale

from .models import SystemSettings


SERVICE_WORKER_JS = """
const CACHE_NAME = "ice-nock-shell-v1";
const APP_SHELL = ["/", "/static/manifest.json", "/static/img/icon-192.png"];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).catch(() => {})
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Network-first for pages (always fresh data for a live POS), cache-first for static assets.
self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  if (req.url.includes("/static/")) {
    event.respondWith(
      caches.match(req).then((cached) => cached || fetch(req).then((res) => {
        const clone = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
        return res;
      }))
    );
    return;
  }

  event.respondWith(
    fetch(req).catch(() => caches.match(req))
  );
});
"""


def service_worker(request):
    return HttpResponse(SERVICE_WORKER_JS, content_type="application/javascript")


def _is_admin(user):
    return user.is_authenticated and user.is_admin_role


@user_passes_test(_is_admin)
def dashboard(request):
    today = timezone.localdate()
    today_sales = Sale.objects.filter(created_at__date=today, status=Sale.Status.COMPLETED)
    month_sales = Sale.objects.filter(
        created_at__year=today.year, created_at__month=today.month, status=Sale.Status.COMPLETED
    )

    today_agg = today_sales.aggregate(
        total=Sum("total"), count=Count("id"), discounts=Sum("discount_total")
    )
    today_qty = sum(i.quantity for s in today_sales.prefetch_related("items") for i in s.items.all())

    month_agg = month_sales.aggregate(
        gross=Sum("subtotal"), discounts=Sum("discount_total"), net=Sum("total")
    )

    products = Product.objects.filter(active=True)
    low_stock = [p for p in products if p.is_low_stock]

    context = {
        "today_total": today_agg["total"] or 0,
        "today_count": today_agg["count"] or 0,
        "today_qty": today_qty,
        "today_discounts": today_agg["discounts"] or 0,
        "current_stock_total": sum(p.current_stock for p in products),
        "low_stock_count": len(low_stock),
        "low_stock_products": low_stock[:8],
        "month_gross": month_agg["gross"] or 0,
        "month_discounts": month_agg["discounts"] or 0,
        "month_net": month_agg["net"] or 0,
        "recent_sales": Sale.objects.select_related("salesperson").order_by("-created_at")[:8],
    }
    return render(request, "admin_dash/dashboard.html", context)


@user_passes_test(_is_admin)
def settings_view(request):
    settings_obj = SystemSettings.load()
    if request.method == "POST":
        settings_obj.company_name = request.POST.get("company_name", settings_obj.company_name)
        settings_obj.address = request.POST.get("address", settings_obj.address)
        settings_obj.phone = request.POST.get("phone", settings_obj.phone)
        settings_obj.email = request.POST.get("email", settings_obj.email)
        settings_obj.receipt_footer = request.POST.get("receipt_footer", settings_obj.receipt_footer)
        settings_obj.currency_code = request.POST.get("currency_code", settings_obj.currency_code)
        settings_obj.currency_symbol = request.POST.get("currency_symbol", settings_obj.currency_symbol)
        try:
            settings_obj.thermal_receipt_width_mm = int(request.POST.get("thermal_receipt_width_mm", 80))
        except ValueError:
            pass
        try:
            settings_obj.low_stock_threshold_default = int(request.POST.get("low_stock_threshold_default", 10))
        except ValueError:
            pass
        settings_obj.save()
        log_action(request.user, "SETTINGS_CHANGE", "Updated system/store settings")
        messages.success(request, "Settings updated.")
    return render(request, "admin_dash/settings.html", {"settings_obj": settings_obj})
