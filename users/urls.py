from django.contrib.auth import views as authentication_views
from django.urls import path

from users import views


app_name = "users"
urlpatterns = [
    path(
        "login/",
        authentication_views.LoginView.as_view(template_name="users/login.html",),
        name="login",
    ),
    path("logout/", authentication_views.LogoutView.as_view(), name="logout"),
    path(
        "password_change/",
        authentication_views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password_change/done/",
        authentication_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path(
        "password_reset/",
        authentication_views.PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        authentication_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        authentication_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        authentication_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path(r"signup/", views.SignupView.as_view(), name="signup"),
    path(
        r"add_to_observed/", views.AddToObservedView.as_view(), name="add_to_observed"
    ),
    path(
        r"remove_from_observed/",
        views.RemoveFromObservedView.as_view(),
        name="remove_from_observed",
    ),
    path("user/<pk>", views.UserProfileDetailView.as_view(), name="user_profile"),
    path("user/<pk>/edit", views.UserProfileUpdateView.as_view(), name="edit_profile"),
    path("banned/<int:user_pk>", views.UserBannedView.as_view(), name="banned"),
    path("ban/", views.BanListView.as_view(), name="ban_list"),
    path("ban/<pk>/update", views.UpdateBanView.as_view(), name="update_ban"),
    path("ban/<pk>/delete", views.DeleteBanView.as_view(), name="delete_ban"),
    path("ban/create", views.CreateBanView.as_view(), name="create_ban"),
]
