from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст, который более 15 символов'
        )

    def setUp(self):
        self.field_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        self.field_helptext = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }

    def test_models_have_correct_object_names(self):
        """Проверка на правильность работы метода __str__"""
        post = PostModelTest.post
        group = PostModelTest.group
        self.assertEqual(group.title, str(group))
        self.assertEqual(post.text[:15], str(post))

    def test_verbose_name(self):
        """Проверка правильности verbose_name"""
        post = PostModelTest.post
        for field, verbose in self.field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, verbose
                )

    def test_helptext(self):
        """Проверка подсказок у полей"""
        post = PostModelTest.post
        for field, helptext in self.field_helptext.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, helptext
                )
