from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.http import urlencode

from posting.exceptions import CannotCreateException


class Board(models.Model):
    created = models.DateField(auto_now_add=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=500, blank=True)
    updated_on = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100, primary_key=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "posting:board_threads_list", kwargs={"board_pk": self.pk},
        )


class Thread(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    closed = models.DateField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    @property
    def starting_post(self):
        return self.post_set.filter(starting_post=True).first()

    @property
    def file(self):
        if self.starting_post:
            return self.starting_post.file

    def get_absolute_url(self):
        return reverse(
            "posting:thread", kwargs={"board_pk": self.board.pk, "pk": self.pk},
        )


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(default="")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    hidden = models.BooleanField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="children",
    )
    refers_to = models.ManyToManyField(
        "self", related_name="referrers_set", blank=True,
    )
    starting_post = models.BooleanField(default=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    file = models.ImageField(blank=True)

    def get_absolute_url(self):
        return "{}?{}".format(
            reverse(
                "posting:thread",
                kwargs={"board_pk": self.thread.board.pk, "pk": self.thread.pk},
            ),
            urlencode({"post_id": self.pk}),
        )

    def save(self, *args, **kwargs):
        if self.starting_post:
            try:
                self.thread.post_set.exclude(id=self.id).get(starting_post=True)
            except Post.DoesNotExist:
                pass
            else:
                raise CannotCreateException(
                    "Multiple starting posts in thread {}".format(self.thread.id)
                )
        return super().save(*args, **kwargs)
