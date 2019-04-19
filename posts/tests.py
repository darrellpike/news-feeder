"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from .models import Post, PostVote
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import timezone
import datetime

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


def create_post(title, days, user):
    time = timezone.now() + datetime.timedelta(days=days)
    return Post.objects.create(submitter=user, title=title, submit_time=time)


class PostsTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')
        login = self.client.login(username='testuser', password='12345')
        post = create_post("Old popular", -2, self.user)
        vote = PostVote(post=post, voter_id=2,  score=100)
        vote.save()
        create_post("New", 0, self.user)
        create_post('Not published', 2, self.user)

    def test_posts_showing_in_list(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Old popular")
        self.assertContains(response, "New")
        self.assertQuerysetEqual(response.context['news'], ['<Post: Old popular>', '<Post: New>'])
        self.assertQuerysetEqual(response.context['latest_news'], ['<Post: New>', '<Post: Old popular>'])
        print("Index page context working correctly")

    def test_latest_posts_showing_in_list(self):
        response = self.client.get(reverse('index_latest'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New")
        self.assertQuerysetEqual(response.context['news'], ['<Post: New>', '<Post: Old popular>'])
        print('Index latest page context working correctly')


class SearchTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')
        self.user2 = get_user_model().objects.create_user(username='testuser2', password='12345')
        popular_post = create_post("Popular", -1, self.user)
        vote1 = PostVote(post=popular_post, voter_id=2, score=1)
        vote2 = PostVote(post=popular_post, voter_id=3, score=1)
        vote1.save()
        vote2.save()
        create_post('Latest', 0, self.user)


    def test_search(self):
        response = self.client.get(reverse('search'), data={'q': "a"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Popular')
        self.assertContains(response, 'Latest')
        self.assertQuerysetEqual(response.context['search_results'], ['<Post: Latest>', '<Post: Popular>'])
        self.assertQuerysetEqual(response.context['top_search_results'], ['<Post: Popular>', '<Post: Latest>'])
        print('Search working correctly')