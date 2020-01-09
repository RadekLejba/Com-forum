from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView


class BaseViewMixin(LoginRequiredMixin):
    login_url = reverse_lazy("users:login")
    redirect_field_name = "redirect_to"


class IndexRedirectView(BaseViewMixin, RedirectView):
    url = reverse_lazy("posting:overboard")
