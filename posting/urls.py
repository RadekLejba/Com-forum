from django.urls import path

from posting import views


app_name = "posting"
urlpatterns = [
    path(r"boards/", views.OverboardView.as_view(), name="overboard"),
    path(
        r"observed/", views.ObservedThreadsListView.as_view(), name="observed_threads"
    ),
    path(r"board/create", views.CreateBoardView.as_view(), name="create_board",),
    path(r"board/<pk>/edit", views.UpdateBoardView.as_view(), name="update_board",),
    path(r"board/<pk>/delete", views.DeleteBoardView.as_view(), name="delete_board",),
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
        r"board/<str:board_pk>/thread/<int:pk>/delete",
        views.DeleteThreadView.as_view(),
        name="delete_thread",
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
    path(
        r"board/<str:board_pk>/thread/<int:thread_pk>/post/<int:pk>/delete",
        views.DeletePostView.as_view(),
        name="delete_post",
    ),
]
