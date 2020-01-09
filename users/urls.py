from django.contrib.auth import views as authentication_views
from django.urls import path

from users.views import SignupView


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
    path(r"signup/", SignupView.as_view(), name="signup"),
]
