from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, View
from django.http import JsonResponse

from forum.views import BaseViewMixin
from posting.models import Thread


class SignupView(CreateView):
    form_class = UserCreationForm
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
