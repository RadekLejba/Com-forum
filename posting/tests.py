import ast
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from posting.models import Board, Thread, Post


class ThreadTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()
        self.thread_name = 'test_thread'
        self.user = User.objects.create(username='testuser01')
        self.user.set_password('testpassword')
        self.user.save()
        self.board = Board.objects.create(
            creator=self.user,
            name='testboard/',
        )
        self.thread1 = Thread.objects.create(
            author=self.user,
            board=self.board,
            name='test_thread_2',
        )
        self.thread2 = Thread.objects.create(
            author=self.user,
            board=self.board,
            name='test_thread_3',
        )
        self.create_thread_url = reverse('posting:create_thread')
        self.thread_details_url = reverse(
            'posting:thread',
            args=[self.thread1.id],
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
            {'board': self.board.id, 'name': self.thread_name},
        )
        thread = Thread.objects.get(name=self.thread_name)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(thread.board, self.board)
        self.assertEqual(thread.name, self.thread_name)
        self.assertEqual(thread.author, self.user)

    def test_thread_details_without_parent_child(self):
        post_1_in_thread = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content='test content 1',
        )
        post_2_in_thread = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content='test content 2',
        )
        post_out_of_thread = Post.objects.create(
            author=self.user,
            thread=self.thread2,
            content='test content 3',
        )
        self.client.login(username=self.user.username, password='testpassword')

        response = self.client.get(self.thread_details_url)
        posts = response.context.get('posts')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(post_1_in_thread, posts)
        self.assertIn(post_2_in_thread, posts)
        self.assertNotIn(post_out_of_thread, posts)

    def test_thread_details_with_parent_child(self):
        post_1 = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content='test content 1',
        )
        post_2 = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content='test content 2',
            parent=post_1,
        )
        post_3 = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content='test content 3',
            parent=post_1,
        )
        post_4 = Post.objects.create(
            author=self.user,
            thread=self.thread1,
            content='test content 4',
        )
        self.client.login(username=self.user.username, password='testpassword')

        response = self.client.get(self.thread_details_url)
        posts = response.context.get('posts')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(post_1, posts)
        self.assertIn(post_2, posts)


class CreatePostTestCase(TestCase):
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
        self.thread = Thread.objects.create(
            author=self.user,
            board=self.board,
            name='test_thread',
        )
        self.create_url = reverse(
            'posting:create_post', args=[self.thread.id, ]
        )
        self.post_content = 'This is test post content'
        self.post = Post.objects.create(
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
        response_refers_thread = self.client.get(
            self.create_url, {'responding_to_the_thread': True}
        )

        self.assertEqual(
            ast.literal_eval(response_refers_to_post.context.get('refers_to')),
            self.post.id,
        )
        self.assertEqual(
            ast.literal_eval(response_with_parent.context.get('parent')),
            self.post.id,
        )
        self.assertEqual(
            ast.literal_eval(
                response_refers_thread.context.get('responding_to_the_thread')
            ),
            True,
        )

    def test_create_post(self):
        self.client.login(username=self.user.username, password='testpassword')

        response = self.client.post(
            self.create_url, {'content': self.post_content}
        )
        post_id = ast.literal_eval(response.url[-1])
        post = Post.objects.get(id=post_id)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post.content, self.post_content)
        self.assertEqual(post.author, self.user)

    def test_respond_to_parent(self):
        self.client.login(username=self.user.username, password='testpassword')

        response = self.client.post(
            self.create_url,
            {'content': self.post_content, 'parent': self.post.id},
        )
        post_id = ast.literal_eval(response.url[-1])
        post = Post.objects.get(id=post_id)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post.content, self.post_content)
        self.assertEqual(post.parent, self.post)
        self.assertEqual(post.author, self.user)

    def test_cant_create_post_with_not_existing_thread(self):
        self.client.login(username=self.user.username, password='testpassword')
        url = reverse('posting:create_post', args=[2137, ])

        response = self.client.post(url, {'content': self.post_content})
        posts = Post.objects.all()

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(len(posts), 1)
