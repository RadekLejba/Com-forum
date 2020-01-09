from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from forum.views import BaseViewMixin
from posting.forms import PostForm
from posting.models import Board, Thread, Post


class OverboardView(BaseViewMixin, ListView):
    model = Thread
    template_name = "posting/overboard.html"


class BoardThreadsListView(BaseViewMixin, ListView):
    template_name = "posting/board_threads_list.html"

    def get_queryset(self):
        return Thread.objects.filter(board=self.kwargs.get("board_pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["board_pk"] = self.kwargs.get("board_pk")
        return context


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
        post_form = PostForm(self.request.POST, thread=thread, author=author,)
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
        parentless_posts = posts.filter(
            thread=self.kwargs.get("pk"), starting_post=False, parent=None,
        ).prefetch_related("children")
        for post in parentless_posts:
            context["posts"][post] = [child for child in post.children.all()]
        return context


class UpdateThreadView(BaseViewMixin, UpdateView):
    model = Thread
    fields = ["name"]

    def get_context_data(self, **kwargs):
        thread = self.get_object()
        context = super().get_context_data(**kwargs)

        context["post_form"] = PostForm(instance=thread.starting_post)
        return context

    def dispatch(self, request, **kwargs):
        thread = self.get_object()
        if thread.author == request.user or request.user.has_perm(
            "posting.change_thread"
        ):
            return super().dispatch(request, **kwargs)
        return HttpResponseForbidden()

    def post(self, request, **kwargs):
        thread = self.get_object()
        post_form = PostForm(
            self.request.POST,
            thread=thread,
            author=thread.starting_post.author,
            instance=thread.starting_post,
        )
        post_form.save()
        return super().post(self, request, **kwargs)


class CreatePostView(BaseViewMixin, CreateView):
    model = Post
    fields = ["content", "parent", "refers_to"]

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


class UpdatePostView(BaseViewMixin, UpdateView):
    model = Post
    fields = ["content"]

    def dispatch(self, request, **kwargs):
        post = self.get_object()
        if post.author == request.user or request.user.has_perm("posting.change_post"):
            return super().dispatch(request, **kwargs)
        return HttpResponseForbidden()
