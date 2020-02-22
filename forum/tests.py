import os

from django.test import TestCase

from posting.models import Board
from forum.templatetags.forum_tags import boards_list


def get_test_image_path():
    return os.path.join(os.path.dirname(__file__), "test_data", "file.jpg")


class TemplateTagsTestCase(TestCase):
    def test_boards_list(self):
        boards = list(Board.objects.all())
        self.assertListEqual(boards, boards_list())
