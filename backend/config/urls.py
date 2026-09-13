from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", include("apps.accounts.health_urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/calls/", include("apps.calls.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/search/", include("apps.search.urls")),
]
