from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from http import HTTPStatus

from posts.models import Group, Post, User


class PostsUrlsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание тестовых объектов"""
        super().setUpClass()

        cls.user = User.objects.create(username='test')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Текст поста тестовой группы',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.post_author = Client()
        self.post_author.force_login(PostsUrlsTests.user)
        self.second_user = User.objects.create(username='NotAuthor')
        self.not_author = Client()
        self.not_author.force_login(self.second_user)

        self.index = reverse('posts:index')
        self.group = reverse(
            'posts:group_list', args=[PostsUrlsTests.group.slug]
        )
        self.profile = reverse(
            'posts:profile', args=[PostsUrlsTests.user.username]
        )
        self.post = reverse('posts:post', args=[PostsUrlsTests.post.pk])
        self.create = reverse('posts:post_create')
        self.add_comment = reverse('posts:add_comment', args=[PostsUrlsTests.post.pk])
        self.edit = reverse('posts:post_edit', args=[PostsUrlsTests.post.pk])
        self.unexpected = '/unexpected-page/'
        self.request_list = [
            [
                self.guest_client.get(self.index),
                HTTPStatus.OK
            ],
            [
                self.guest_client.get(self.group),
                HTTPStatus.OK
            ],
            [
                self.guest_client.get(self.profile),
                HTTPStatus.OK
            ],
            [
                self.guest_client.get(self.post),
                HTTPStatus.OK
            ],
            [
                self.guest_client.get(self.create),
                HTTPStatus.FOUND
            ],
            [
                self.not_author.get(self.create),
                HTTPStatus.OK
            ],
            [
                self.post_author.get(self.edit),
                HTTPStatus.OK
            ],
            [
                self.not_author.get(self.edit),
                HTTPStatus.FOUND
            ],
            [
                self.guest_client.get(self.unexpected),
                HTTPStatus.NOT_FOUND
            ],
            [
                self.guest_client.get(self.add_comment),
                HTTPStatus.FOUND
            ],
            [
                self.post_author.get(self.add_comment),
                HTTPStatus.FOUND
            ]
        ]
        self.redirect_list = [
            [self.guest_client.get(self.create), '/auth/login/?next=/create/'],
            [self.guest_client.get(self.edit), self.post],
            [self.not_author.get(self.edit), self.post],
            [self.guest_client.get(self.add_comment), '/auth/login/?next=/posts/1/comment/'],
            [self.not_author.get(self.add_comment), self.post]
        ]
        self.url_to_template = [
            [self.index, 'posts/index.html'],
            [self.group, 'posts/group_list.html'],
            [self.profile, 'posts/profile.html'],
            [self.post, 'posts/post_detail.html'],
            [self.create, 'posts/create_post.html'],
            [self.edit, 'posts/create_post.html'],
            [self.unexpected, 'core/404.html']
        ]

    def test_urls(self):
        """Тестирование страниц на правильность отработки"""
        for request, status in self.request_list:
            with self.subTest(
                request_status=request.status_code,
                expected_status=status
            ):
                self.assertEqual(request.status_code, status)

    def test_urls_redirect(self):
        """Тестирование на перенаправление при отказе доступа"""
        for request, adress in self.redirect_list:
            with self.subTest(test=request, adress=adress):
                self.assertRedirects(request, adress)

    def test_template_match(self):
        """Проверка использования верных шаблонов"""
        # Для проверки главной необходимо освободить кэш
        cache.clear()
        for url, template in self.url_to_template:
            with self.subTest(url=url, template=template):
                request = self.post_author.get(url)
                self.assertTemplateUsed(request, template)
