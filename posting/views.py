from django.http import (
    HttpResponseNotFound,
    HttpResponseForbidden,
)
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy, reverse

from forum.views import BaseViewMixin
from posting.forms import PostForm
from posting.models import Board, Thread, Post


class CrudPermissionViewMixin(BaseViewMixin):
    permission = ""

    def dispatch(self, request, **kwargs):
        obj = self.get_object()
        if obj.author == request.user or request.user.has_perm(self.permission):
            return super().dispatch(request, **kwargs)
        return HttpResponseForbidden()

    def post(self, request, **kwargs):
        if request.user.userprofile.is_banned:
            return redirect(reverse("users:banned", args=[request.user.id]))
        return super().post(request, **kwargs)


class ThreadListViewMixin(BaseViewMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["board_pk"] = self.kwargs.get("board_pk")
        context[
            "observed_threads"
        ] = self.request.user.userprofile.observed_threads.all()
        return context


class ObservedThreadsListView(ThreadListViewMixin):
    template_name = "posting/overboard.html"

    def get_queryset(self):
        return self.request.user.userprofile.observed_threads.all()


class OverboardView(ThreadListViewMixin):
    model = Thread
    template_name = "posting/overboard.html"
    ordering = ["-created_on"]


class BoardThreadsListView(ThreadListViewMixin):
    template_name = "posting/board_threads_list.html"

    def get_queryset(self):
        return Thread.objects.filter(board=self.kwargs.get("board_pk"))


class CreateThreadView(BaseViewMixin, CreateView):
    model = Thread
    fields = ["name"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_form"] = PostForm()
        return context

    def form_valid(self, form):
        try:
            board = Board.objects.get(pk=self.kwargs.get("board_pk"))
        except Board.DoesNotExist:
            return HttpResponseNotFound("<h4>Board not found</h4>")
        author = self.request.user
        form.instance.board = board
        form.instance.author = author
        thread = form.save()
        post_form = PostForm(
            self.request.POST, self.request.FILES, thread=thread, author=author,
        )
        post_form.instance.starting_post = True
        post_form.save()
        return redirect(thread)


class ThreadDetailView(BaseViewMixin, DetailView):
    model = Thread

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = Post.objects.filter(thread=self.kwargs.get("pk"))
        context["board_pk"] = self.kwargs.get("board_pk")
        context["posts"] = {}
        try:
            context["starting_post"] = posts.get(
                thread=self.kwargs.get("pk"), starting_post=True
            )
        except Post.DoesNotExist:
            context["starting_post"] = None
        parentless_posts = (
            posts.filter(
                thread=self.kwargs.get("pk"), starting_post=False, parent=None,
            )
            .order_by("created_on")
            .prefetch_related("children")
        )
        for post in parentless_posts:
            context["posts"][post] = [child for child in post.children.all()]
        return context


class UpdateThreadView(CrudPermissionViewMixin, UpdateView):
    model = Thread
    fields = ["name"]
    permission = "posting.change_thread"

    def get_context_data(self, **kwargs):
        thread = self.get_object()
        context = super().get_context_data(**kwargs)

        context["post_form"] = PostForm(instance=thread.starting_post)
        return context

    def post(self, request, **kwargs):
        thread = self.get_object()
        post_form = PostForm(
            self.request.POST,
            thread=thread,
            author=thread.starting_post.author,
            instance=thread.starting_post,
        )
        post_form.save()
        return super().post(request, **kwargs)


class DeleteThreadView(CrudPermissionViewMixin, DeleteView):
    model = Thread
    permission = "posting.delete_thread"
    template_name = "posting/confirm_delete.html"

    def dispatch(self, request, **kwargs):
        self.success_url = reverse_lazy(
            "posting:board_threads_list", kwargs={"board_pk": kwargs.get("board_pk")},
        )
        return super().dispatch(request, **kwargs)


class CreatePostView(BaseViewMixin, CreateView):
    model = Post
    fields = ["content", "parent", "refers_to", "file"]

    def form_valid(self, form):
        thread_pk = self.kwargs.get("thread_pk")
        try:
            form.instance.thread = Thread.objects.get(id=thread_pk)
        except Thread.DoesNotExist:
            return HttpResponseNotFound("<h4>Thread not found</h4>")

        form.instance.author = self.request.user

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["refers_to"] = self.request.GET.get("refers_to")
        context["parent"] = self.request.GET.get("parent")
        return context


class UpdatePostView(CrudPermissionViewMixin, UpdateView):
    model = Post
    fields = ["content"]
    permission = "posting.change_post"


class DeletePostView(CrudPermissionViewMixin, DeleteView):
    model = Post
    permission = "posting.delete_post"
    template_name = "posting/confirm_delete.html"

    def dispatch(self, request, **kwargs):
        thread_pk = self.get_object().thread.pk
        self.success_url = reverse_lazy(
            "posting:thread",
            kwargs={"board_pk": kwargs.get("board_pk"), "pk": thread_pk},
        )
        return super().dispatch(request, **kwargs)
