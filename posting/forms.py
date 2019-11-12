from django.forms import ModelForm

from posting.models import Post


class PostForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.thread = kwargs.pop('thread', None)
        self.author = kwargs.pop('author', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Post
        fields = ['content', 'parent', 'refers_to']

    def save(self):
        post = super().save(commit=False)
        post.thread = self.thread
        post.author = self.author
        post.save()
        return post
