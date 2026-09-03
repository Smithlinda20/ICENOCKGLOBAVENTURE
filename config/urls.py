from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from core.views import service_worker

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="accounts:login", permanent=False), name="root"),
    path("service-worker.js", service_worker, name="service_worker"),
    path("django-admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("sales.urls")),
    path("", include("products.urls")),
    path("", include("discounts.urls")),
    path("", include("inventory.urls")),
    path("", include("reports.urls")),
    path("", include("audit.urls")),
    path("", include("core.urls")),
    path("api/", include("sales.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
