from django import template

from posting.models import Board


register = template.Library()


@register.simple_tag
def boards_list():
    return list(Board.objects.all())
