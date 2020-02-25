import ast
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from freezegun import freeze_time

from forum.tests import get_test_image_path
from posting.exceptions import CannotCreateException
from posting.forms import PostForm
from posting.models import Board, Thread, Post


class PostingTestMixin(TestCase):
    def setUp(self):
        self.image_path = get_test_image_path()
        self.file = open(self.image_path, "rb")
        User = get_user_model()
        moderator_permissions = [
            Permission.objects.get(name="Can change post"),
            Permission.objects.get(name="Can delete post"),
            Permission.objects.get(name="Can change thread"),
            Permission.objects.get(name="Can delete thread"),
        ]
        self.client = Client()
        self.user = User.objects.create(username="testuser01")
        self.password = "testpassword"
        self.user.set_password(self.password)
        self.user.save()
        self.user2 = User.objects.create(username="testuser02")
        self.user2.set_password(self.password)
        self.user2.save()
        self.moderator = User.objects.create(username="moderatoruser")
        self.moderator.set_password(self.password)
        for permission in moderator_permissions:
            self.moderator.user_permissions.add(permission)
        self.moderator.save()
        self.board_name = "testboard"
        self.board = Board.objects.create(creator=self.user, name=self.board_name,)
        self.thread_name = "test_thread"
        self.post_content = "This is test post content"
        self.board_threads_list_url = reverse(
            "posting:board_threads_list", kwargs={"board_pk": self.board.pk},
        )
        self.observed_threads_list_url = reverse("posting:observed_threads",)

    def tearDown(self):
        self.file.close()


class ModelsTestCase(PostingTestMixin):
    def test_thread_absolute_url(self):
        thread = Thread.objects.create(
            author=self.user, board=self.board, name="test_thread",
        )

        self.assertEqual(
            thread.get_absolute_url(),
            reverse(
                "posting:thread", kwargs={"board_pk": self.board.pk, "pk": thread.pk},
            ),
        )

    def test_thread_starting_post(self):
        thread = Thread.objects.create(
            author=self.user, board=self.board, name="test_thread",
        )
        post = Post.objects.create(
            author=self.user, content="lorem ipsum", thread=thread, starting_post=True,
        )
        Post.objects.create(
            author=self.user, content="doesent matter", thread=thread,
        )

        self.assertEqual(thread.starting_post, post)

    @freeze_time("2012-01-14 03:00:00", as_arg=True)
    def test_get_time_passed(frozen_time, self):
        thread = Thread.objects.create(
            author=self.user, board=self.board, name="test_thread",
        )
        post = Post.objects.create(
            author=self.user, content="lorem ipsum", thread=thread,
        )

        frozen_time.move_to("2012-01-14 03:00:01")
        self.assertEqual(post.time_passed_since_creation, "1 second")

        frozen_time.move_to("2012-01-14 03:02:00")
        self.assertEqual(post.time_passed_since_creation, "2 minutes")

        frozen_time.move_to("2012-01-14 07:00:00")
        self.assertEqual(post.time_passed_since_creation, "4 hours")

        frozen_time.move_to("2012-01-20 03:00:00")
        self.assertEqual(post.time_passed_since_creation, "6 days")

    def test_update_flag_after_update(self):
        thread = Thread.objects.create(
            author=self.user, board=self.board, name="test_thread",
        )
        post = Post.objects.create(
            author=self.user, content="lorem ipsum", thread=thread,
        )

        self.assertFalse(post.updated)

        post.content = "test"
        post.save()

        self.assertTrue(post.updated)


class FormsTestCase(PostingTestMixin):
    def test_post_form(self):
        self.thread = Thread.objects.create(
            author=self.user, board=self.board, name=self.thread_name,
        )
        parent_post = Post.objects.create(author=self.user, thread=self.thread)
        ref_post1 = Post.objects.create(author=self.user, thread=self.thread)
        ref_post2 = Post.objects.create(author=self.user, thread=self.thread)
        data = {
            "content": self.post_content,
            "parent": parent_post.pk,
            "refers_to": [ref_post1.pk, ref_post2.pk],
        }

        form = PostForm(data, thread=self.thread, author=self.user)
        post = form.save()
        form.save_m2m()

        self.assertEqual(post.content, data["content"])
        self.assertEqual(post.parent.pk, data["parent"])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.thread, self.thread)
        self.assertListEqual(
            [referrer.pk for referrer in post.refers_to.all()], data["refers_to"],
        )


class BoardViewsTestCase(PostingTestMixin):
    def setUp(self):
        super().setUp()
        self.create_board_url = reverse("posting:create_board")
        self.update_board_url = reverse("posting:update_board", args=[self.board.pk])
        self.delete_board_url = reverse("posting:delete_board", args=[self.board.pk])
        self.board_name = "testcreatedboard"
        self.description = "test description"
        self.board2 = Board.objects.create(creator=self.user, name="testboard2",)
        self.thread = Thread.objects.create(
            author=self.user, board=self.board, name=self.thread_name,
        )
        self.thread2 = Thread.objects.create(
            author=self.user, board=self.board, name=self.thread_name,
        )
        self.thread3 = Thread.objects.create(
            author=self.user, board=self.board2, name=self.thread_name,
        )

    def test_board_threads_list(self):
        self.client.login(username=self.user.username, password=self.password)
        expected_threads = [self.thread, self.thread2]

        response = self.client.get(self.board_threads_list_url)

        self.assertCountEqual(list(response.context["thread_list"]), expected_threads)
        self.assertEqual(response.context["board_pk"], self.board.pk)

    def test_board_threads_list_with_observed(self):
        self.client.login(username=self.user.username, password=self.password)
        self.user.userprofile.observed_threads.add(self.thread)
        self.user.userprofile.observed_threads.add(self.thread3)

        response = self.client.get(self.board_threads_list_url)

        self.assertListEqual(
            list(response.context["observed_threads"]), [self.thread, self.thread3]
        )

    def test_observed_threads_list(self):
        self.client.login(username=self.user.username, password=self.password)
        self.user.userprofile.observed_threads.add(self.thread)
        self.user.userprofile.observed_threads.add(self.thread3)

        response = self.client.get(self.observed_threads_list_url)

        self.assertListEqual(
            list(response.context["object_list"]), [self.thread, self.thread3]
        )

    def test_create_board_with_permissions(self):
        create_thread_permission = Permission.objects.get(name="Can add board")
        self.user.user_permissions.add(create_thread_permission)
        self.user.save()
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.create_board_url,
            {"name": self.board_name, "description": self.description},
        )
        board = Board.objects.get(name=self.board_name)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(board.description, self.description)

    def test_cant_create_board_without_permissions(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.create_board_url,
            {"name": self.board_name, "description": self.description},
        )
        board = Board.objects.filter(name=self.board_name)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(board.count(), 0)

    def test_cant_update_board_without_permissions(self):
        new_description = "new description"
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.update_board_url, {"description": new_description}
        )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_board_with_permissions(self):
        create_thread_permission = Permission.objects.get(name="Can change board")
        self.user.user_permissions.add(create_thread_permission)
        self.user.save()
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.update_board_url, {"description": "new description"}
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_cant_delete_board_without_permissions(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(self.delete_board_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_board_with_permissions(self):
        create_thread_permission = Permission.objects.get(name="Can delete board")
        self.user.user_permissions.add(create_thread_permission)
        self.user.save()
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(self.delete_board_url)
        board = Board.objects.filter(name=self.board_name)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(board.count(), 0)


class PostViewsTestCase(PostingTestMixin):
    def setUp(self):
        super().setUp()
        self.thread = Thread.objects.create(
            author=self.user, board=self.board, name=self.thread_name,
        )
        self.thread_details_url = reverse(
            "posting:thread", kwargs={"board_pk": self.board.pk, "pk": self.thread.pk},
        )
        self.create_url = reverse(
            "posting:create_post",
            kwargs={"board_pk": self.board.pk, "thread_pk": self.thread.pk},
        )
        self.post = Post.objects.create(author=self.user, thread=self.thread,)
        self.post2 = Post.objects.create(author=self.user, thread=self.thread,)
        self.update_post_url = reverse(
            "posting:update_post",
            kwargs={
                "board_pk": self.board.pk,
                "thread_pk": self.thread.pk,
                "pk": self.post.pk,
            },
        )
        self.delete_post_url = reverse(
            "posting:delete_post",
            kwargs={
                "board_pk": self.board.pk,
                "thread_pk": self.thread.pk,
                "pk": self.post.pk,
            },
        )

    def test_context(self):
        self.client.login(username=self.user.username, password=self.password)

        response_refers_to_post = self.client.get(
            self.create_url, {"refers_to": self.post.id}
        )
        response_with_parent = self.client.get(
            self.create_url, {"parent": self.post.id}
        )

        self.assertEqual(
            ast.literal_eval(response_refers_to_post.context.get("refers_to")),
            self.post.id,
        )
        self.assertEqual(
            ast.literal_eval(response_with_parent.context.get("parent")), self.post.id,
        )

    def test_create_post(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(self.create_url, {"content": self.post_content})
        post_id = ast.literal_eval(response.url.split("post_id=")[1])
        post = Post.objects.get(id=post_id)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post.content, self.post_content)
        self.assertEqual(post.author, self.user)

    def test_create_post_with_parent_and_referrers(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.create_url,
            {
                "content": self.post_content,
                "parent": self.post.id,
                "refers_to": [self.post.id, self.post2.id],
            },
        )
        post_id = ast.literal_eval(response.url.split("post_id=")[1])
        post = Post.objects.get(id=post_id)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post.content, self.post_content)
        self.assertEqual(post.parent, self.post)
        self.assertEqual(post.author, self.user)

    def test_create_with_non_existing_thread(self):
        self.client.login(username=self.user.username, password=self.password)
        post_quantity = Post.objects.all().count()
        non_existing_thread_url = reverse(
            "posting:create_post",
            kwargs={"board_pk": self.board.pk, "thread_pk": 2137},
        )

        response = self.client.post(
            non_existing_thread_url, {"content": self.post_content,},
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Post.objects.all().count(), post_quantity)

    def test_cant_create_multiple_starting_posts(self):
        self.post.starting_post = True
        self.post.save()

        with self.assertRaises(CannotCreateException) as exp:
            Post.objects.create(
                author=self.user, thread=self.thread, starting_post=True,
            )
        self.assertEqual(
            "Multiple starting posts in thread {}".format(self.thread.id),
            str(exp.exception),
        )

    def test_edit_post_by_author(self):
        self.client.login(username=self.user.username, password=self.password)

        response_get = self.client.get(self.update_post_url)
        response_post = self.client.post(
            self.update_post_url, {"content": self.post_content,},
        )

        self.assertEqual(response_get.status_code, HTTPStatus.OK)
        self.assertEqual(response_post.status_code, HTTPStatus.FOUND)

    def test_edit_post_by_user_with_permissions(self):
        self.client.login(username=self.moderator.username, password=self.password)
        response_get = self.client.get(self.update_post_url)
        response_post = self.client.post(
            self.update_post_url, {"content": self.post_content,},
        )

        self.assertEqual(response_get.status_code, HTTPStatus.OK)
        self.assertEqual(response_post.status_code, HTTPStatus.FOUND)

    def test_edit_post_by_user_without_permissions(self):
        self.client.login(username=self.user2.username, password=self.password)
        response_get = self.client.get(self.update_post_url)
        response_post = self.client.post(
            self.update_post_url, {"content": self.post_content,},
        )

        self.assertEqual(response_get.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response_post.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_post_by_author(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.delete(self.delete_post_url)

        self.assertEqual(response.url, self.thread_details_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_delete_post_by_user_with_permissions(self):
        self.client.login(username=self.moderator.username, password=self.password)

        response = self.client.delete(self.delete_post_url)

        self.assertEqual(response.url, self.thread_details_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_delete_post_by_user_without_permissions(self):
        self.client.login(username=self.user2.username, password=self.password)

        response = self.client.delete(self.delete_post_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class ThreadViewsTestCase(PostingTestMixin):
    def setUp(self):
        super().setUp()
        self.thread1 = Thread.objects.create(
            author=self.user, board=self.board, name="test_thread_1",
        )
        self.thread2 = Thread.objects.create(
            author=self.user, board=self.board, name="test_thread_2",
        )
        self.create_thread_url = reverse(
            "posting:create_thread", kwargs={"board_pk": self.board.pk},
        )
        self.thread_details_url = reverse(
            "posting:thread", kwargs={"board_pk": self.board.pk, "pk": self.thread1.pk},
        )
        self.update_thread_url = reverse(
            "posting:update_thread",
            kwargs={"board_pk": self.board.pk, "pk": self.thread1.pk},
        )
        self.delete_thread_url = reverse(
            "posting:delete_thread",
            kwargs={"board_pk": self.board.pk, "pk": self.thread1.pk},
        )
        self.updated_content = "This is updated content"

    def test_authentication(self):
        self.client.post(
            self.create_thread_url, {"board": self.board.pk, "name": self.thread_name},
        )
        details_response = self.client.get(self.thread_details_url)
        create_response = self.client.get(self.create_thread_url)

        with self.assertRaises(Thread.DoesNotExist):
            Thread.objects.get(name=self.thread_name),
        self.assertEqual(details_response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            details_response.url,
            "{}?redirect_to={}".format(reverse("users:login"), self.thread_details_url),
        )
        self.assertEqual(create_response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            create_response.url,
            "{}?redirect_to={}".format(reverse("users:login"), self.create_thread_url),
        )

    def test_create_thread(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.create_thread_url,
            {
                "name": self.thread_name,
                "content": self.post_content,
                "file": self.file,
            },
        )
        thread = Thread.objects.get(name=self.thread_name)
        starting_post = Post.objects.get(thread=thread, starting_post=True)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(thread.board, self.board)
        self.assertEqual(thread.name, self.thread_name)
        self.assertEqual(thread.author, self.user)
        self.assertEqual(starting_post.content, self.post_content)
        self.assertIsNotNone(starting_post.file)

        # tearDown
        starting_post.file.storage.delete(starting_post.file.name)

    def test_thread_details_without_parent_child(self):
        post_1_in_thread = Post.objects.create(
            author=self.user, thread=self.thread1, content=self.post_content,
        )
        post_2_in_thread = Post.objects.create(
            author=self.user, thread=self.thread1, content=self.post_content,
        )
        post_out_of_thread = Post.objects.create(
            author=self.user, thread=self.thread2, content=self.post_content,
        )
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.thread_details_url)
        posts = response.context.get("posts")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(post_1_in_thread, posts)
        self.assertIn(post_2_in_thread, posts)
        self.assertNotIn(post_out_of_thread, posts)

    def test_thread_details_with_parent_child(self):
        starting_post = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
            starting_post=True,
        )
        post_1 = Post.objects.create(
            author=self.user, thread=self.thread1, content=self.post_content,
        )
        post_2 = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
            parent=post_1,
        )
        post_3 = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
            parent=post_1,
        )
        post_4 = Post.objects.create(
            author=self.user, thread=self.thread1, content=self.post_content,
        )
        self.client.login(username=self.user.username, password=self.password)
        expected_posts = {
            post_1: [post_2, post_3],
            post_4: [],
        }

        response = self.client.get(self.thread_details_url)
        posts = response.context.get("posts")

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertDictEqual(expected_posts, posts)
        self.assertEqual(starting_post, response.context.get("starting_post"))
        self.assertNotIn(starting_post, posts)

    def test_get_update_thread_corect_data(self):
        post = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
            starting_post=True,
        )
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.get(self.update_thread_url)
        post_form = response.context.get("post_form")

        self.assertEqual(post_form.instance.content, post.content)

    def test_update_thread_by_author(self):
        post = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
            starting_post=True,
        )
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(
            self.update_thread_url,
            {"name": self.thread_name, "content": self.updated_content},
        )
        post.refresh_from_db()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post.content, self.updated_content)

    def test_update_thread_by_user_with_permission(self):
        post = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
            starting_post=True,
        )
        self.client.login(username=self.moderator.username, password=self.password)

        response = self.client.post(
            self.update_thread_url,
            {"name": self.thread_name, "content": self.updated_content},
        )
        post.refresh_from_db()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post.content, self.updated_content)

    def test_update_thread_by_user_without_permission(self):
        post = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
            starting_post=True,
        )
        self.client.login(username=self.user2.username, password=self.password)

        response = self.client.post(
            self.update_thread_url,
            {"name": self.thread_name, "content": self.updated_content},
        )
        post.refresh_from_db()

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(post.content, self.post_content)

    def test_delete_thread_by_author(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.delete(self.delete_thread_url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, self.board_threads_list_url)

    def test_delete_thread_by_user_with_permission(self):
        self.client.login(username=self.moderator.username, password=self.password)

        response = self.client.delete(self.delete_thread_url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, self.board_threads_list_url)

    def test_delete_thread_by_user_without_permission(self):
        self.client.login(username=self.user2.username, password=self.password)

        response = self.client.delete(self.delete_thread_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
