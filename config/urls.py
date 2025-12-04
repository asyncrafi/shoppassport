from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/shop/", include("apps.shop.urls")),
    path("api/core/", include("apps.core.urls")),
    path("api/shopadmin/", include("apps.shopadmin.urls")),
    path("api/shopowner/", include("apps.shopowner.urls")),
    path("api/shopper/", include("apps.shopper.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


