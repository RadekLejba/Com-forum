from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from posting.models import Thread


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    observed_threads = models.ManyToManyField(Thread, blank=True)

    def __str__(self):
        return "{} profile".format(self.user)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
