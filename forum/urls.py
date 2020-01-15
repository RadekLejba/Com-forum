from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from forum.views import IndexRedirectView


urlpatterns = [
    path(r"", IndexRedirectView.as_view(), name="index"),
    path(r"users/", include("users.urls")),
    path(r"posting/", include("posting.urls")),
    path(r"admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
