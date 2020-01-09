from django.test import TestCase

from posting.models import Board
from forum.templatetags.forum_tags import boards_list


class TemplateTagsTestCase(TestCase):
    def test_boards_list(self):
        boards = list(Board.objects.all())
        self.assertListEqual(boards, boards_list())
