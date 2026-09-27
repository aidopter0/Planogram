from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.accounts.spa_views import LoginPageView, SpaView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.api.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("login/", LoginPageView.as_view(), name="login"),
    path("", SpaView.as_view(), name="spa"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
