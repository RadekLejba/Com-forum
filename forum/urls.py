from django.urls import include, path
from django.contrib import admin

from forum.views import IndexRedirectView


urlpatterns = [
    path(r'', IndexRedirectView.as_view(), name='index'),
    path(r'users/', include('users.urls')),
    path(r'posting/', include('posting.urls')),
    path(r'admin/', admin.site.urls),
]
