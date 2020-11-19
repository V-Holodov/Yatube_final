from django.test import TestCase
from posts.models import Post, Group, User


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='StasBasov')
        cls.group = Group.objects.create(
            title='Группа',
            )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group
            )

    def test_post_verbose_name(self):
        """verbose_name полей модели post совпадает с ожидаемым."""
        post = ModelTest.post
        field_verboses = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Картинка',
            }
        for value, expected in field_verboses.items():
            with self.subTest():
                self.assertEqual(
                    post._meta.get_field(value).verbose_name,
                    expected
                    )

    def test_post_help_text(self):
        """help_text полей модели post совпадает с ожидаемым."""
        post = ModelTest.post
        field_verboses = {
            'text': 'Поле обязательно для ввода текста',
            'group': 'Выбирите группу',
            'image': 'Загрузите картинку',
            }
        for value, expected in field_verboses.items():
            with self.subTest():
                self.assertEqual(
                    post._meta.get_field(value).help_text,
                    expected
                    )

    def test_group_verbose_name(self):
        """verbose_name полей модели group совпадает с ожидаемым."""
        group = ModelTest.group
        field_verboses = {
            'title': 'Группа',
            'slug': 'Слаг'
            }
        for value, expected in field_verboses.items():
            with self.subTest():
                self.assertEqual(
                    group._meta.get_field(value).verbose_name,
                    expected
                    )

    def test_group_help_text(self):
        """help_text полей модели group совпадает с ожидаемым."""
        group = ModelTest.group
        field_verboses = {
            'title': 'Название группы',
            'slug': ('Укажите адрес для страницы задачи. Используйте только '
                     'латиницу, цифры, дефисы и знаки подчёркивания')
            }
        for value, expected in field_verboses.items():
            with self.subTest():
                self.assertEqual(
                    group._meta.get_field(value).help_text,
                    expected
                    )

    def test_post_metod_str(self):
        """__str__  post - это строчка с содержимым post.text[:15]"""
        post = ModelTest.post
        text = post.text[:15]
        self.assertEqual(text, str(post))

    def test_group_metod_str(self):
        """__str__  group - это строчка с содержимым group.title"""
        group = ModelTest.group
        title = group.title
        self.assertEqual(title, str(group))

    def test_title_convert_to_slug(self):
        """save преобразует в slug содержимое поля title."""
        group = ModelTest.group
        slug = group.slug
        self.assertEquals(slug, 'gruppa')
