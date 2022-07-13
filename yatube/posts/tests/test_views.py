import tempfile
import shutil
from random import randint
from urllib import request
from django.test import TestCase, Client, override_settings
from django.test import Client, TestCase
from django import forms
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


from posts.models import Group, Post, User
from yatube.settings import BASE_DIR, POSTS_PER_PAGE


POSTS_ON_LAST_PAGE = randint(1, POSTS_PER_PAGE - 1)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.user = User.objects.create(username='Billy')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Просто описание'
        )
        cls.post = Post.objects.create(
            text='Рандомный текст',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorised_client = Client()
        self.authorised_client.force_login(ViewsTests.user)
        cache.clear()

    def test_context_post(self):
        """Весь контекст передан на страницу поста"""
        response = self.authorised_client.get(
            reverse('posts:post', args=[ViewsTests.post.pk])
        )
        self.assertEqual(response.context['post'], ViewsTests.post)

    def test_context_group(self):
        """Проверка контекста Странички группы"""
        response = self.authorised_client.get(
            reverse('posts:group_list', args=[ViewsTests.group.slug])
        )
        self.assertEqual(response.context['group'], ViewsTests.group)

    def test_edit_post(self):
        """проверка форм для создания и редактирования поста"""
        response = self.authorised_client.get(
            reverse('posts:post_edit', args=[ViewsTests.post.pk])
        )
        form_fiels = [
            ['text', forms.fields.CharField],
            ['group', forms.fields.ChoiceField],
            ['image', forms.fields.ImageField]
        ]
        for field, type in form_fiels:
            with self.subTest(field=field):
                self.assertIsInstance(
                    response.context['form'].fields[field], type
                )

    def test_cache_of_index(self):
        """Тестирую работу кэша"""
        post = Post.objects.create(
            text='В чем смысл моей жизни?',
            author=self.user
        )
        first_response = self.authorised_client.get(
            reverse('posts:index')
        ).content.decode()
        post.delete()
        second_response = self.authorised_client.get(
            reverse('posts:index')
        ).content.decode()
        self.assertEqual(first_response, second_response)
        cache.clear()
        third_response = self.authorised_client.get(
            reverse('posts:index')
        ).content.decode()
        self.assertNotEqual(first_response, third_response)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Van')
        cls.group = Group.objects.create(
            title='Просто группа',
            slug='cool-place',
            description='Многопостовая группа'
        )

    def setUp(self):
        super().setUp()
        self.auth_client = Client()
        self.auth_client.force_login(PaginatorTests.user)
        self.posts = [
            Post.objects.create(
                text=f'Текст номер {i+1}',
                author=PaginatorTests.user,
                group=PaginatorTests.group
            )for i in range(POSTS_PER_PAGE + POSTS_ON_LAST_PAGE)
        ]
        cache.clear()

    def test_context_index_first_page(self):
        """Весь контекст отображается на главной и работает паджинатор"""
        response = self.auth_client.get(reverse('posts:index'))
        posts_reversed = self.posts[::-1]
        for i, post in enumerate(posts_reversed[:POSTS_PER_PAGE]):
            with self.subTest(text=post.text):
                self.assertEqual(
                    response.context['page_obj'][i].text, post.text
                )
                self.assertEqual(
                    response.context['page_obj'][i].author, post.author
                )
                self.assertEqual(
                    response.context['page_obj'][i].group, post.group
                )
        self.assertEqual(
            response.context['page_obj'].end_index(), POSTS_PER_PAGE
        )

    def test_context_index_second_page(self):
        """Проверка паджинатора, передается от 11 до 19 постов"""
        response = self.auth_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            response.context['page_obj'].paginator.count % POSTS_PER_PAGE,
            Post.objects.count() % POSTS_PER_PAGE
        )

    def test_context_group_first_page(self):
        """Весь контекст отображается на главной и работает паджинатор"""
        response = self.auth_client.get(
            reverse('posts:group_list', args=[PaginatorTests.group.slug])
        )
        posts_reversed = self.posts[::-1]
        for i, post in enumerate(posts_reversed[:POSTS_PER_PAGE]):
            with self.subTest(text=post.text):
                self.assertEqual(
                    response.context['page_obj'][i].text, post.text
                )
                self.assertEqual(
                    response.context['page_obj'][i].author, post.author
                )
                self.assertEqual(
                    response.context['page_obj'][i].group, PaginatorTests.group
                )
        self.assertEqual(
            response.context['page_obj'].end_index(), POSTS_PER_PAGE
        )

    def test_context_group_second_page(self):
        """Проверка паджинатора, в группе от 11 до 19 постов"""
        response = self.auth_client.get(
            reverse(
                'posts:group_list',
                args=[PaginatorTests.group.slug]) + '?page=2'
        )
        self.assertEqual(
            response.context['page_obj'].paginator.count % POSTS_PER_PAGE,
            POSTS_ON_LAST_PAGE
        )

    def test_context_profile_first_page(self):
        """Весь контекст передан странице пользователя и работает паджинатор"""
        response = self.auth_client.get(
            reverse('posts:profile', args=[PaginatorTests.user])
        )
        posts_reversed = self.posts[::-1]
        for i, post in enumerate(posts_reversed[:POSTS_PER_PAGE]):
            with self.subTest(text=post.text):
                self.assertEqual(
                    response.context['page_obj'][i].text, post.text
                )
                self.assertEqual(
                    response.context['page_obj'][i].author, PaginatorTests.user
                )
                self.assertEqual(
                    response.context['page_obj'][i].group, post.group
                )
        self.assertEqual(
            response.context['page_obj'].end_index(), POSTS_PER_PAGE
        )

    def test_context_profile_second_page(self):
        """Проверка паджинатора, у пользователя от 11 до 19 постов"""
        response = self.auth_client.get(
            reverse(
                'posts:profile',
                args=[PaginatorTests.user]) + '?page=2'
        )
        self.assertEqual(
            response.context['page_obj'].paginator.count % POSTS_PER_PAGE,
            POSTS_ON_LAST_PAGE
        )
