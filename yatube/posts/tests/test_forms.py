import tempfile
import shutil

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from yatube import settings
from posts.forms import PostForm
from posts.models import Group, User, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostCreationForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Test_subject')
        cls.group = Group.objects.create(
            title='Тест',
            slug='test',
            description='Тестовое описание'
        )
        cls.edit_post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            author=TestPostCreationForm.user
        )
        cls.second_group = Group.objects.create(
            title='Тест группа номер два',
            slug='test_edit',
            description='Тестовое описание 2'
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        edit_uploaded = SimpleUploadedFile(
            name='big.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        self.new_post_data = {
            'text': 'Новый пост',
            'group': self.group.pk,
            'image': uploaded
        }
        self.form_edit = {
            'text': 'Текст изменился',
            'group': self.second_group.id,
            'image': edit_uploaded
        }
        self.form_comment = {
            'text': 'Пишу что хочу'
        }

    def test_post_creation(self):
        """Проверка записи валидного поста"""
        post_count = Post.objects.count()
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=self.new_post_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=[self.user])
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        latest_post = Post.objects.latest('pub_date')
        latest_post_check = {
            latest_post.text: self.new_post_data['text'],
            latest_post.group.id: self.new_post_data['group'],
            latest_post.image: 'posts/small.gif'
        }
        for field, value in latest_post_check.items():
            with self.subTest(field=field):
                self.assertEqual(field, value)

    def test_post_edit(self):
        """Проверка изменения поста без создания новой записи"""
        pre_edit_post_count = Post.objects.count()
        response = self.auth_client.post(
            reverse(
                'posts:post_edit',
                args=[self.edit_post.pk]
            ),
            data=self.form_edit,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post',
                args=[self.edit_post.pk]
            )
        )
        self.assertEqual(Post.objects.count(), pre_edit_post_count)
        get_post = Post.objects.get(id=self.edit_post.id)
        edited_post_check = {
            get_post.text: self.form_edit['text'],
            get_post.group.id: self.form_edit['group'],
            get_post.image: 'posts/big.gif'
        }
        for field, value in edited_post_check.items():
            with self.subTest(field=field):
                self.assertEqual(field, value)

    def test_add_comment(self):
        pre_comment_count = self.edit_post.comments.count()
        response = self.auth_client.post(
            reverse(
                'posts:add_comment',
                args=[self.edit_post.pk]
            ),
            data=self.form_comment,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post',
                args=[self.edit_post.pk]
            )
        )
        post_comment_count = self.edit_post.comments.count()
        self.assertEqual(
            pre_comment_count + 1,
            post_comment_count
        )
        new_comment = self.edit_post.comments.latest('created').text
        self.assertEqual(
            new_comment,
            self.form_comment['text']
        )
