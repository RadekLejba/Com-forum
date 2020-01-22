from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from posting.models import Board, Thread


class UserProfileTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_userprofile_creation(self):
        user = self.User.objects.create(username="testuser01")

        self.assertIsNotNone(user.userprofile)


class ObservedThreadTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()
        self.user = User.objects.create(username="testuser01")
        self.password = "testpassword"
        self.user.set_password(self.password)
        self.user.save()
        self.add_to_observed_url = reverse("users:add_to_observed",)
        self.remove_from_observed_url = reverse("users:remove_from_observed",)
        self.board = Board.objects.create(creator=self.user, name="testboard",)
        self.thread_name = "test_thread"
        self.thread = Thread.objects.create(
            author=self.user, board=self.board, name="test_thread",
        )
        self.response_not_exist = {"result": "error", "error": "thread does not exist"}

    def test_add_to_observed(self):
        expected_response = {"result": "success", "success": "created"}
        self.client.login(username=self.user.username, password=self.password)

        response_add_to_observed = self.client.post(
            self.add_to_observed_url, {"id": self.thread.id}
        )
        observed_thread = self.user.userprofile.observed_threads.all()

        self.assertDictEqual(response_add_to_observed.json(), expected_response)
        self.assertEqual(len(observed_thread), 1)

    def test_add_to_observed_not_exiting_thread(self):
        self.client.login(username=self.user.username, password=self.password)

        response_add_to_observed = self.client.post(
            self.add_to_observed_url, {"id": self.thread.id + 1}
        )
        observed_thread = self.user.userprofile.observed_threads.all()

        self.assertDictEqual(response_add_to_observed.json(), self.response_not_exist)
        self.assertEqual(len(observed_thread), 0)

    def test_remove_from_observed(self):
        expected_response = {"result": "success", "success": "deleted"}
        self.client.login(username=self.user.username, password=self.password)

        self.user.userprofile.observed_threads.add(self.thread)
        response_remove_from_observed = self.client.post(
            self.remove_from_observed_url, {"id": self.thread.id}
        )
        observed_thread = self.user.userprofile.observed_threads.all()

        self.assertDictEqual(response_remove_from_observed.json(), expected_response)
        self.assertEqual(len(observed_thread), 0)
