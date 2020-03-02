from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
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
        return reverse("posting:board_threads_list", kwargs={"board_pk": self.pk},)


class Thread(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    closed = models.DateField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)
    last_post_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def starting_post(self):
        return self.post_set.filter(starting_post=True).first()

    @property
    def file(self):
        if self.starting_post:
            return self.starting_post.file

    @property
    def post_count(self):
        return self.post_set.count() - 1

    def update_most_recent_post_creation_date(self):
        try:
            self.last_post_added = (
                self.post_set.all().order_by("-created_on")[0].created_on
            )
            self.save()
        except IndexError:
            return

    def get_absolute_url(self):
        return reverse(
            "posting:thread", kwargs={"board_pk": self.board.pk, "pk": self.pk},
        )


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(default="")
    created_on = models.DateTimeField(auto_now_add=True)
    updated = models.BooleanField(default=False)
    updated_on = models.DateTimeField(auto_now=True)
    hidden = models.BooleanField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="children",
    )
    refers_to = models.ForeignKey(
        "self",
        related_name="referrers_set",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    starting_post = models.BooleanField(default=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    file = models.ImageField(blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_content = self.content

    def check_plural(self, number):
        if number != 1:
            return "s"
        return ""

    def timedelta_to_humanified_string(self, passed_time):
        seconds = passed_time.seconds
        if passed_time <= timedelta(minutes=1):
            return "{} second{}".format(seconds, self.check_plural(seconds))
        elif passed_time <= timedelta(hours=1):
            minutes = seconds // 60
            return "{} minute{}".format(minutes, self.check_plural(minutes))
        elif passed_time <= timedelta(days=1):
            hours = seconds // 3600
            return "{} hour{}".format(hours, self.check_plural(hours))

        days = passed_time.days
        return "{} day{}".format(days, self.check_plural(days))

    @property
    def time_passed_since_creation(self):
        passed_time = timezone.now() - self.created_on
        return self.timedelta_to_humanified_string(passed_time)

    @property
    def time_passed_since_edition(self):
        if self.updated:
            passed_time = timezone.now() - self.updated_on
            return self.timedelta_to_humanified_string(passed_time)

    def get_absolute_url(self):
        return "{}?{}".format(
            reverse(
                "posting:thread",
                kwargs={"board_pk": self.thread.board.pk, "pk": self.thread.pk},
            ),
            urlencode({"post_id": self.pk}),
        )

    def save(self, *args, **kwargs):
        if self.original_content:
            if not self.updated and self.content != self.original_content:
                self.updated = True

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


@receiver(post_save, sender=Post)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        instance.thread.update_most_recent_post_creation_date()
