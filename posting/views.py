from django.http import HttpResponseNotFound
from django.views.generic import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy

from forum.views import BaseViewMixin
from posting.models import Board, Thread, Post


# Will be replaced in near future with rest API
class TemporaryIndexView(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['boards'] = Board.objects.all()
        return context


class CreateThreadView(BaseViewMixin, CreateView):
    model = Thread
    fields = ['board', 'name']
    success_url = reverse_lazy('posting:overboard')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ThreadDetailView(BaseViewMixin, DetailView):
    model = Thread

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = Post.objects.filter(thread=self.kwargs.get('pk'))

        for post in posts:
            import ipdb; ipdb.set_trace()
        return context


class CreatePostView(BaseViewMixin, CreateView):
    model = Post
    fields = ['content']

    def form_valid(self, form):
        parent = self.request.POST.get('parent')
        refers_to = self.request.POST.get('refers_to')
        thread_pk = self.kwargs.get('pk')
        try:
            if parent:
                form.instance.parent = Post.objects.get(id=parent)
            if refers_to:
                form.instance.refers_to = Post.objects.get(id=refers_to)
            if thread_pk:
                form.instance.thread = Thread.objects.get(id=thread_pk)
        except Thread.DoesNotExist:
            return HttpResponseNotFound('<h4>Thread not found</h4>')
        except Post.DoesNotExist:
            return HttpResponseNotFound('<h4>Post not found</h4>')

        form.instance.author = self.request.user
        form.instance.responding_to_the_thread = self.kwargs.get(
            'responding_to_the_thread',
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['refers_to'] = self.request.GET.get('refers_to')
        context['parent'] = self.request.GET.get('parent')
        context['responding_to_the_thread'] = self.request.GET.get(
            'responding_to_the_thread'
        )
        return context


class OverboardView(BaseViewMixin, TemporaryIndexView):
    model = Thread
    template_name = 'posting/overboard.html'
