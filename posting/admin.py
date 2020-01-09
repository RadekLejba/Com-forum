from django.contrib import admin

from posting.models import Board, Post, Thread


class PostInline(admin.TabularInline):
    model = Post


class ThreadAdmin(admin.ModelAdmin):
    inlines = [
        PostInline,
    ]


admin.site.register(Board)
admin.site.register(Post)
admin.site.register(Thread, ThreadAdmin)
