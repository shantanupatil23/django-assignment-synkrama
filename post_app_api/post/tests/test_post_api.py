"""
Tests for post APIs.
"""
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from post.models import Post
from post.serializers import PostSerializer
from post.views import CustomPagination

POSTS_URL = reverse('post:post-list')


def detail_url(post_id):
    """Create and return a post detail URL."""
    return reverse('post:post-detail', args=[post_id])


def create_post(author, **params):
    """Create and return a sample post."""
    defaults = {
        'title': 'Sample post title',
        'body': 'Sample post body',
    }
    defaults.update(params)

    post = Post.objects.create(author=author, **defaults)
    return post


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PrivatePostApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')
        self.client.force_authenticate(self.user)

    def test_retrieve_posts(self):
        """Test retrieving a list of posts."""
        create_post(author=self.user)
        create_post(author=self.user)

        res = self.client.get(POSTS_URL)

        posts = Post.objects.all().order_by('-id')
        serializer = PostSerializer(posts, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], serializer.data)

    def test_post_list_limited_to_user(self):
        """Test list of posts is limited to authenticated user."""
        other_user = create_user(email='other@example.com', password='test123')
        create_post(author=other_user)
        create_post(author=self.user)

        res = self.client.get(POSTS_URL)

        posts = Post.objects.filter(author=self.user)
        serializer = PostSerializer(posts, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], serializer.data)

    def test_get_post_detail(self):
        """Test get post detail."""
        post = create_post(author=self.user)
        post = create_post(author=self.user)

        url = detail_url(post.id)
        res = self.client.get(url)

        serializer = PostSerializer(post)

        self.assertEqual(res.data, serializer.data)

    def test_create_post(self):
        """Test creating a post."""
        payload = {
            'author': self.user,
            'title': 'Sample post title',
            'body': 'Sample post body',
        }
        res = self.client.post(POSTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(post, k), v)
        self.assertEqual(post.author, self.user)

    def test_partial_update(self):
        """Test partial update of a post."""
        original_body = 'Sample post body'
        post = create_post(
            author=self.user,
            title='Sample post title',
            body=original_body,
        )

        payload = {'title': 'New post title'}
        url = detail_url(post.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, payload['title'])
        self.assertEqual(post.body, original_body)
        self.assertEqual(post.author, self.user)

    def test_full_update(self):
        """Test full update of post."""
        post = create_post(
            author=self.user,
            title='Sample post title',
            body='Sample post body',
        )

        payload = {
            'title': 'New post title',
            'body': 'New post body',
        }
        url = detail_url(post.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(post, k), v)
        self.assertEqual(post.author, self.user)

    def test_update_user_returns_error(self):
        """Test changing the post user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        post = create_post(author=self.user)

        payload = {'user': new_user.id}
        url = detail_url(post.id)
        self.client.patch(url, payload)

        post.refresh_from_db()
        self.assertEqual(post.author, self.user)

    def test_delete_post(self):
        """Test deleting a post successful."""
        post = create_post(author=self.user)

        url = detail_url(post.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=post.id).exists())

    def test_post_other_users_post_error(self):
        """Test trying to delete another users post gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        post = create_post(author=new_user)

        url = detail_url(post.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Post.objects.filter(id=post.id).exists())

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')  # noqa:E501
    def test_create_post_sends_email_notification(self):
        payload = {
            'author': self.user,
            'title': 'Sample post title',
            'body': 'Sample post body',
        }
        self.client.post(POSTS_URL, payload)

        email_subject = 'New post created'
        email_message = (f"Hi Django User {payload['author']},"
                         f"\n\nYour post \"{payload['title']}\""
                         " has been created successfully.")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, email_subject)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(mail.outbox[0].body, email_message)

    def test_retrieve_paginated_posts(self):
        """Test retrieving a list of paginated posts."""
        number_of_posts = 27
        page_size = CustomPagination.page_size
        for _ in range(number_of_posts):
            create_post(author=self.user)

        posts = Post.objects.all().order_by('-id')
        serializer = PostSerializer(posts, many=True)

        page_number = 0
        for start_index in range(0,number_of_posts, page_size):
            page_number += 1
            res = self.client.get(POSTS_URL, {'page': page_number})
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data['results'], serializer.data[start_index:start_index+page_size])

    def test_filter_by_title(self):
        """Test filtering posts by title."""
        search_title = 'A catchy title'
        create_post(author=self.user, title=search_title)
        create_post(author=self.user, title='A boring title')

        res = self.client.get(POSTS_URL, {'title': search_title})

        posts = Post.objects.filter(title=search_title).order_by('-id')
        serializer = PostSerializer(posts, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], serializer.data)

    def test_filter_by_body(self):
        """Test filtering posts by body."""
        search_body = 'A catchy body'
        create_post(author=self.user, body=search_body)
        create_post(author=self.user, body='A boring body')

        res = self.client.get(POSTS_URL, {'body': search_body})

        posts = Post.objects.filter(body=search_body).order_by('-id')
        serializer = PostSerializer(posts, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], serializer.data)
