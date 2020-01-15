from django import template

from posting.models import Board


register = template.Library()


@register.simple_tag
def boards_list():
    return list(Board.objects.all())


@register.simple_tag
def item_or_parent_id(item):
    if item.parent:
        return item.parent.id
    return item.id
