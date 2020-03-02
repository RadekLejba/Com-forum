from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import View, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.http import HttpResponseForbidden, JsonResponse

from forum.views import BaseViewMixin
from posting.models import Thread
from users.forms import CustomBanForm, ExtendedUserCreationForm
from users.models import Ban, UserProfile


class SignupView(CreateView):
    form_class = ExtendedUserCreationForm
    success_url = reverse_lazy("users:login")
    template_name = "users/signup.html"


class AddToObservedView(BaseViewMixin, View):
    def post(self, request):
        thread_id = request.POST.get("id")

        try:
            thread = Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            return JsonResponse({"result": "error", "error": "thread does not exist"})

        request.user.userprofile.observed_threads.add(thread)

        return JsonResponse({"result": "success", "success": "created"})


class RemoveFromObservedView(BaseViewMixin, View):
    def post(self, request):
        thread_id = request.POST.get("id")

        try:
            thread = Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            return JsonResponse({"result": "error", "error": "thread does not exist"})

        request.user.userprofile.observed_threads.remove(thread)
        return JsonResponse({"result": "success", "success": "deleted"})


class UserProfileDetailView(BaseViewMixin, DetailView):
    model = UserProfile


class UserProfileUpdateView(BaseViewMixin, UpdateView):
    model = UserProfile
    fields = ["avatar"]

    def dispatch(self, request, **kwargs):
        obj = self.get_object()
        if obj.user == request.user:
            return super().dispatch(request, **kwargs)
        return HttpResponseForbidden()


class BanListView(BaseViewMixin, PermissionRequiredMixin, ListView):
    model = Ban
    permission_required = "users.view_ban"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_list = context.get("object_list")
        context["object_list"] = [item for item in object_list if item.is_active]
        return context


class CreateBanView(BaseViewMixin, PermissionRequiredMixin, CreateView):
    model = Ban
    form_class = CustomBanForm
    permission_required = "users.add_ban"
    success_url = reverse_lazy("users:ban_list",)

    def get_initial(self):
        initial = super().get_initial()
        initial = initial.copy()
        initial["user"] = self.request.GET.get("user_pk")
        return initial


class UpdateBanView(BaseViewMixin, PermissionRequiredMixin, UpdateView):
    model = Ban
    form_class = CustomBanForm
    permission_required = "users.change_ban"
    success_url = reverse_lazy("users:ban_list",)


class DeleteBanView(BaseViewMixin, PermissionRequiredMixin, DeleteView):
    model = Ban
    permission_required = "users.delete_ban"
    success_url = reverse_lazy("users:ban_list",)


class UserBannedView(TemplateView):
    template_name = "users/banned.html"

    def get(self, request, **kwargs):
        user_pk = kwargs.get("user_pk")
        if self.request.user.pk != user_pk:
            return HttpResponseForbidden()
        return super().get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_bans = self.request.user.ban_set.all()
        active_bans = [ban for ban in user_bans if ban.is_active]
        active_bans.sort(key=lambda x: x.created, reverse=True)

        try:
            context["most_recent_ban"] = active_bans[0]
        except IndexError:
            pass

        return context
