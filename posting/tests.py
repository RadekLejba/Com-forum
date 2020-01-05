import ast
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from posting.exceptions import CannotCreateException
from posting.forms import PostForm
from posting.models import Board, Thread, Post


class PostingTestMixin(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()
        self.user = User.objects.create(username='testuser01')
        self.user.set_password('testpassword')
        self.user.save()
        self.board = Board.objects.create(
            creator=self.user,
            name='testboard/',
        )
        self.thread_name = 'test_thread'
        self.post_content = 'This is test post content'


class ModelsTestCase(PostingTestMixin):
    def test_thread_absolute_url(self):
        thread = Thread.objects.create(
            author=self.user,
            board=self.board,
            name='test_thread',
        )

        self.assertEqual(
            thread.get_absolute_url(),
            reverse(
                'posting:thread',
                kwargs={'board_pk': self.board.pk, 'pk': thread.pk},
            )
        )

    def test_thread_starting_post(self):
        thread = Thread.objects.create(
            author=self.user,
            board=self.board,
            name='test_thread',
        )
        post = Post.objects.create(
            author=self.user,
            content='lorem ipsum',
            thread=thread,
            starting_post=True,
        )
        Post.objects.create(
            author=self.user,
            content='doesent matter',
            thread=thread,
        )

        self.assertEqual(
            thread.starting_post,
            post
        )


class FormsTestCase(PostingTestMixin):
    def test_thread_form(self):
        self.thread = Thread.objects.create(
            author=self.user,
            board=self.board,
            name=self.thread_name,
        )
        parent_post = Post.objects.create(author=self.user, thread=self.thread)
        ref_post1 = Post.objects.create(author=self.user, thread=self.thread)
        ref_post2 = Post.objects.create(author=self.user, thread=self.thread)
        data = {
            'content': self.post_content,
            'parent': parent_post.pk,
            'refers_to': [ref_post1.pk, ref_post2.pk],
        }

        form = PostForm(data, thread=self.thread, author=self.user)
        post = form.save()
        form.save_m2m()

        self.assertEqual(post.content, data['content'])
        self.assertEqual(post.parent.pk, data['parent'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.thread, self.thread)
        self.assertListEqual(
            [referrer.pk for referrer in post.refers_to.all()],
            data['refers_to'],
        )


class BoardViewsTestCase(PostingTestMixin):
    def setUp(self):
        super().setUp()
        self.board_threads_list_url = reverse(
            'posting:board_threads_list',
            kwargs={'board_pk': self.board.pk},
        )
        self.board2 = Board.objects.create(
            creator=self.user,
            name='testboard2/',
        )
        self.thread = Thread.objects.create(
            author=self.user,
            board=self.board,
            name=self.thread_name,
        )
        self.thread2 = Thread.objects.create(
            author=self.user,
            board=self.board,
            name=self.thread_name,
        )
        self.thread3 = Thread.objects.create(
            author=self.user,
            board=self.board2,
            name=self.thread_name,
        )

    def test_board_threads_list(self):
        self.client.login(username=self.user.username, password='testpassword')
        expected_threads = [self.thread, self.thread2]

        response = self.client.get(self.board_threads_list_url)

        self.assertListEqual(
            list(response.context['thread_list']), expected_threads
        )
        self.assertEqual(response.context['board_pk'], self.board.pk)


class CreatePostTestCase(PostingTestMixin):
    def setUp(self):
        super().setUp()
        self.thread = Thread.objects.create(
            author=self.user,
            board=self.board,
            name=self.thread_name,
        )
        self.create_url = reverse(
            'posting:create_post',
            kwargs={'board_pk': self.board.pk, 'thread_pk': self.thread.pk},
        )
        self.post = Post.objects.create(
            author=self.user,
            thread=self.thread,
        )
        self.post2 = Post.objects.create(
            author=self.user,
            thread=self.thread,
        )

    def test_context(self):
        self.client.login(username=self.user.username, password='testpassword')

        response_refers_to_post = self.client.get(
            self.create_url, {'refers_to': self.post.id}
        )
        response_with_parent = self.client.get(
            self.create_url, {'parent': self.post.id}
        )

        self.assertEqual(
            ast.literal_eval(response_refers_to_post.context.get('refers_to')),
            self.post.id,
        )
        self.assertEqual(
            ast.literal_eval(response_with_parent.context.get('parent')),
            self.post.id,
        )

    def test_create_post(self):
        self.client.login(username=self.user.username, password='testpassword')

        response = self.client.post(
            self.create_url, {'content': self.post_content}
        )
        post_id = ast.literal_eval(response.url.split('post_id=')[1])
        post = Post.objects.get(id=post_id)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post.content, self.post_content)
        self.assertEqual(post.author, self.user)

    def test_create_post_with_parent_and_referrers(self):
        self.client.login(username=self.user.username, password='testpassword')

        response = self.client.post(
            self.create_url,
            {
                'content': self.post_content,
                'parent': self.post.id,
                'refers_to': [self.post.id, self.post2.id]
            },
        )
        post_id = ast.literal_eval(response.url.split('post_id=')[1])
        post = Post.objects.get(id=post_id)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post.content, self.post_content)
        self.assertEqual(post.parent, self.post)
        self.assertEqual(post.author, self.user)

    def test_create_with_non_existing_thread(self):
        self.client.login(username=self.user.username, password='testpassword')
        post_quantity = Post.objects.all().count()
        non_existing_thread_url = reverse(
            'posting:create_post',
            kwargs={'board_pk': self.board.pk, 'thread_pk': 2137},
        )

        response = self.client.post(
            non_existing_thread_url,
            {
                'content': self.post_content,
            },
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Post.objects.all().count(), post_quantity)

    def test_cant_create_multiple_starting_posts(self):
        self.post.starting_post = True
        self.post.save()

        with self.assertRaises(CannotCreateException) as exp:
            Post.objects.create(
                author=self.user,
                thread=self.thread,
                starting_post=True,
            )
        self.assertEqual(
            'Multiple starting posts in thread {}'.format(self.thread.id),
            str(exp.exception),
        )


class ThreadViewsTestCase(PostingTestMixin):
    def setUp(self):
        super().setUp()
        self.thread1 = Thread.objects.create(
            author=self.user,
            board=self.board,
            name='test_thread_1',
        )
        self.thread2 = Thread.objects.create(
            author=self.user,
            board=self.board,
            name='test_thread_2',
        )
        self.create_thread_url = reverse(
            'posting:create_thread',
            kwargs={'board_pk': self.board.pk},
        )
        self.thread_details_url = reverse(
            'posting:thread',
            kwargs={'board_pk': self.board.pk, 'pk': self.thread1.pk},
        )

    def test_authentication(self):
        self.client.post(
            self.create_thread_url,
            {'board': self.board.id, 'name': self.thread_name},
        )
        details_response = self.client.get(self.thread_details_url)
        create_response = self.client.get(self.create_thread_url)

        with self.assertRaises(Thread.DoesNotExist):
            Thread.objects.get(name=self.thread_name),
        self.assertEqual(details_response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            details_response.url,
            '{}?redirect_to={}'.format(
                reverse('users:login'), self.thread_details_url
            ),
        )
        self.assertEqual(create_response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            create_response.url,
            '{}?redirect_to={}'.format(
                reverse('users:login'), self.create_thread_url
            ),
        )

    def test_create_thread(self):
        self.client.login(username=self.user.username, password='testpassword')

        response = self.client.post(
            self.create_thread_url,
            {'name': self.thread_name, 'content': self.post_content}
        )
        thread = Thread.objects.get(name=self.thread_name)
        starting_post = Post.objects.get(thread=thread, starting_post=True)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(thread.board, self.board)
        self.assertEqual(thread.name, self.thread_name)
        self.assertEqual(thread.author, self.user)
        self.assertEqual(starting_post.content, self.post_content)

    def test_thread_details_without_parent_child(self):
        post_1_in_thread = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
        )
        post_2_in_thread = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
        )
        post_out_of_thread = Post.objects.create(
            author=self.user,
            thread=self.thread2,
            content=self.post_content,
        )
        self.client.login(username=self.user.username, password='testpassword')
        response = self.client.get(self.thread_details_url)
        posts = response.context.get('posts')

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
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
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
            author=self.user,
            thread=self.thread1,
            content=self.post_content,
        )
        self.client.login(username=self.user.username, password='testpassword')
        expected_posts = {
            post_1: [post_2, post_3],
            post_4: [],
        }

        response = self.client.get(self.thread_details_url)
        posts = response.context.get('posts')

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertDictEqual(expected_posts, posts)
        self.assertEqual(starting_post, response.context.get('starting_post'))
        self.assertNotIn(starting_post, posts)
