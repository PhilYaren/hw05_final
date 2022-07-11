from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Follow, Post, User


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.following = User.objects.create(username='Spector')
        cls.follower = User.objects.create(username='Vasya')
        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.following
        )

    def setUp(self):
        self.author = Client()
        self.author.force_login(self.following)
        self.user_follower = Client()
        self.user_follower.force_login(self.follower)
        self.follow_author = reverse(
            'posts:profile_follow', args=[self.following]
        )
        self.author_profile = reverse('posts:profile', args=[self.following])
        self.unfollow_author = reverse(
            'posts:profile_unfollow', args=[self.following]
        )
        self.follow_index_with_post = reverse('posts:follow_index')

    def test_add_following(self):
        """Проверка на работу подписки на авторов"""
        pre_follow_count = Follow.objects.count()
        response = self.user_follower.get(self.follow_author)
        self.assertRedirects(
            response, self.author_profile
        )
        after_follow_count = Follow.objects.count()
        self.assertEqual(pre_follow_count + 1, after_follow_count)
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=self.following
            ).exists()
        )

    def test_unfollow(self):
        """Проверка отписки от автора"""
        Follow.objects.create(
            user=self.follower,
            author=self.following
        )
        pre_unfollow_count = Follow.objects.count()
        response = self.user_follower.get(self.unfollow_author)
        self.assertRedirects(
            response, self.author_profile
        )
        after_unfollow_count = Follow.objects.count()
        self.assertEqual(pre_unfollow_count - 1, after_unfollow_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.following
            ).exists()
        )

    def test_post_in_follow(self):
        """Пост отображается у подписчика"""
        Follow.objects.create(
            user=self.follower,
            author=self.following
        )
        response = self.user_follower.get(self.follow_index_with_post)
        self.assertIn(self.post, response.context['page_obj'])

    def test_post_not_in_follow(self):
        """Пост не отображается у не подписавшихся"""
        response = self.user_follower.get(self.follow_index_with_post)
        self.assertNotIn(self.post, response.context['page_obj'])
