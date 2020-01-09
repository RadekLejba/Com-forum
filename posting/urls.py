from django.urls import path

from posting import views


app_name = "posting"
urlpatterns = [
    path(r"boards/", views.OverboardView.as_view(), name="overboard"),
    path(
        r"board/<str:board_pk>/threads",
        views.BoardThreadsListView.as_view(),
        name="board_threads_list",
    ),
    path(
        r"board/<str:board_pk>/create_thread/",
        views.CreateThreadView.as_view(),
        name="create_thread",
    ),
    path(
        r"board/<str:board_pk>/thread/<int:pk>/",
        views.ThreadDetailView.as_view(),
        name="thread",
    ),
    path(
        r"board/<str:board_pk>/thread/<int:pk>/update",
        views.UpdateThreadView.as_view(),
        name="update_thread",
    ),
    path(
        r"board/<str:board_pk>/thread/<int:thread_pk>/create_post/",
        views.CreatePostView.as_view(),
        name="create_post",
    ),
    path(
        r"board/<str:board_pk>/thread/<int:thread_pk>/post/<int:pk>/update",
        views.UpdatePostView.as_view(),
        name="update_post",
    ),
]
