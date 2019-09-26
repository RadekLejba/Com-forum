from django.urls import include, path
from django.contrib import admin

from forum.views import IndexView


urlpatterns = [
    path(r'', IndexView.as_view(), name='index'),
    path(r'users/', include('users.urls')),
    path(r'admin/', admin.site.urls),
]
