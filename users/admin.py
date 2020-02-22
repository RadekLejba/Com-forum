from django.contrib import admin

from users.models import UserProfile, Ban


admin.site.register(UserProfile)
admin.site.register(Ban)
