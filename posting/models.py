from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.timezone import now


class Board(models.Model):
    created = models.DateField(default=now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=500, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Thread(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    closed = models.DateField(null=True, blank=True)
    content = models.TextField(default='')
    created = models.DateField(default=now)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(default='')
    created = models.DateField(default=now)
    hidden = models.BooleanField(null=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children',
    )
    refers_to = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    responding_to_the_thread = models.BooleanField(null=True, blank=True)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return '{}?{}'.format(
            reverse('posting:thread', args=[str(self.thread.id)]),
            urlencode({'post_id': self.pk}),
        )
