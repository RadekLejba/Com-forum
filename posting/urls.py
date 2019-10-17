from django.urls import path

from posting.views import (
    CreatePostView,
    CreateThreadView,
    OverboardView,
    ThreadDetailView,
)


app_name = 'posting'
urlpatterns = [
    path(r'threads/', OverboardView.as_view(), name='overboard'),
    path(r'thread/<pk>', ThreadDetailView.as_view(), name='thread'),
    path(
        r'thread/<pk>/create_post/',
        CreatePostView.as_view(),
        name='create_post'
    ),
    path(r'create_thread/', CreateThreadView.as_view(), name='create_thread'),
]
