from datetime import timedelta
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from freezegun import freeze_time

from forum.tests import get_test_image_path
from posting.models import Board, Thread
from users.models import Ban


class UserProfileModelTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_userprofile_creation(self):
        user = self.User.objects.create(username="testuser01")

        self.assertIsNotNone(user.userprofile)

    def test_is_banned(self):
        user = self.User.objects.create(username="testuser01")

        with freeze_time("2012-01-14 03:00:00"):
            Ban.objects.create(user=user, duration=timedelta(days=3), reason="test")
            Ban.objects.create(user=user, duration=timedelta(days=4), reason="test")

            self.assertTrue(user.userprofile.is_banned)
        self.assertFalse(user.userprofile.is_banned)


class BanModelTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create(username="testuser01")

    def test_ban_end_date(self):
        with freeze_time("2012-01-14 03:00:00"):
            ban = Ban.objects.create(
                user=self.user, duration=timedelta(days=2, hours=3)
            )

            self.assertTrue(ban.is_active)

        self.assertFalse(ban.is_active)


class ViewsTestsMixin(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()
        self.user = User.objects.create(username="testuser01")
        self.password = "testpassword"
        self.user.set_password(self.password)
        self.user.save()
        self.create_ban_url = reverse("users:create_ban",)
        self.ban_list_url = reverse("users:ban_list",)
        self.user_profile_url = reverse(
            "users:user_profile", kwargs={"pk": self.user.pk}
        )
        self.update_user_profile_url = reverse(
            "users:edit_profile", kwargs={"pk": self.user.pk}
        )
        self.test_duration = timedelta(days=2, hours=3)
        self.test_reason = "test reason"
        moderator_permissions = [
            Permission.objects.get(name="Can view ban"),
            Permission.objects.get(name="Can add ban"),
            Permission.objects.get(name="Can change ban"),
            Permission.objects.get(name="Can delete ban"),
        ]
        self.moderator = User.objects.create(username="moderatoruser")
        self.moderator.set_password(self.password)
        for permission in moderator_permissions:
            self.moderator.user_permissions.add(permission)
        self.moderator.save()


class BanCRUDTestCase(ViewsTestsMixin):
    def test_moderator_can_see_ban_list(self):
        self.client.login(username=self.moderator.username, password=self.password)

        response = self.client.get(self.ban_list_url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_moderator_can_create_ban(self):
        self.client.login(username=self.moderator.username, password=self.password)

        response = self.client.post(
            self.create_ban_url,
            {
                "user": self.user.pk,
                "duration": self.test_duration,
                "reason": self.test_reason,
            },
        )
        ban = Ban.objects.filter(user=self.user).first()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(ban.user, self.user)
        self.assertEqual(ban.duration, self.test_duration)
        self.assertEqual(ban.reason, self.test_reason)

    def test_create_view_initial_values(self):
        self.client.login(username=self.moderator.username, password=self.password)

        response = self.client.get(self.create_ban_url, {"user_pk": self.user.pk,},)

        self.assertEqual(int(response.context["form"].initial["user"]), self.user.pk)


class ObservedThreadTestCase(ViewsTestsMixin):
    def setUp(self):
        super().setUp()
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


class UserProfileTestCase(ViewsTestsMixin):
    def setUp(self):
        super().setUp()
        self.image_path = get_test_image_path()
        self.file = open(self.image_path, "rb")
        self.update_form = {
            "avatar": self.file,
        }

    def tearDown(self):
        self.file.close()

    def test_get_user_avatar(self):
        self.assertEqual(self.user.userprofile.avatar_url, settings.DEFAULT_AVATAR_URL)

    def test_get_userprofile(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.get(self.user_profile_url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_update_userprofile_view(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.get(self.update_user_profile_url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_only_owner_can_update_userprofile_view(self):
        self.client.login(username=self.moderator.username, password=self.password)

        response_get = self.client.get(self.update_user_profile_url)
        response_post = self.client.post(
            self.update_user_profile_url, self.update_form
        )

        self.assertEqual(response_get.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response_post.status_code, HTTPStatus.FORBIDDEN)
