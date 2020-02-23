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
        bans = self.user.ban_set.filter()
        for ban in bans:
            if ban.is_active:
                return True

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar else settings.DEFAULT_AVATAR_URL

    def __str__(self):
        return "{} profile".format(self.user)

    def get_absolute_url(self):
        return reverse(
            "users:user", args=[self.pk],
        )


class Ban(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=150)
    created = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField()

    @property
    def is_active(self):
        return (self.created + self.duration) > timezone.now()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
