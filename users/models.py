from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from posting.models import Thread


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    observed_threads = models.ManyToManyField(Thread, blank=True)
    avatar = models.ImageField(blank=True)

    @property
    def is_banned(self):
        active_bans = [ban for ban in self.user.ban_set.all() if ban.is_active]
        if active_bans:
            return True
        return False

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar else settings.DEFAULT_AVATAR_URL

    def __str__(self):
        return "{} profile".format(self.user)

    def get_absolute_url(self):
        return reverse("users:user_profile", args=[self.pk],)


class Ban(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=150)
    created = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField()

    @property
    def is_active(self):
        return (self.created + self.duration) > timezone.now()

    @property
    def time_left(self):
        time_left = (self.created + self.duration) - timezone.now()
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return "{} hours {} minutes and {} seconds left".format(hours, minutes, seconds)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
