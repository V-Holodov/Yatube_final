from posts.views import new_post
from django.contrib.auth import get_user_model
from django.http import response
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()
        cls.group = Group.objects.create(title='тестгруппа')
        cls.templates_url_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts', kwargs={'slug': cls.group.slug}),
            'new_post.html': reverse('new_post')
            }

    def test_homepage(self):
        """main page request test"""
        response = self.unauthorized_client.get('/')
        self.assertEqual(
            response.status_code,
            200,
            'Главная страница не доступна'
            )

    def test_group_page(self):
        """group page availability"""
        response = self.unauthorized_client.get(
            reverse(
                'group_posts',
                kwargs={'slug': StaticURLTests.group.slug}
                )
            )
        self.assertEqual(
            response.status_code,
            200,
            'Страница группы не доступна'
            )

    def test_new_post_page(self):
        """availability of the post add page for an authorized user"""
        response = self.authorized_client.get(
            reverse('new_post')
            )
        self.assertEqual(
            response.status_code,
            200,
            ('Страница добавления нового поста'
             'не доступна авторизованному пользователю')
            )

    def test_new_post_page_redirect(self):
        """redirect an unauthorized user when trying to add a new post"""
        response = self.unauthorized_client.get(
            reverse('new_post'),
            follow=True
            )
        self.assertRedirects(
            response,
            '/auth/login/?next=/new/',
            msg_prefix=(
                'Незарегистрированный пользователь не перенаправляется'
                'на страницу входа при попытке создать пост'
                )
            )

    def test_force_login(self):
        """checking the request for a new post form by an authorized user"""
        response = self.authorized_client.get('/new/')
        self.assertEqual(
            response.status_code,
            200,
            'Страница нового поста не доступна зарегистрированному пользователю'
            )

    def test_unauthorized_user_newpage(self):
        """checking the availability of the new/ page
        for an unauthorized user"""
        response = self.unauthorized_client.get('/new/', follow=False)
        self.assertRedirects(
            response, '/auth/login/?next=/new/',
            status_code=302, target_status_code=200,
            msg_prefix=(
                'Страница добавления поста доступна'
                ' незарегистрированному пользователю'
                )
            )


    def test_404(self):
        """checking whether the server returns a 404 error"""
        response = self.authorized_client.get('about/___')
        self.assertEqual(
            response.status_code,
            404,
            'Сервер не возвращает код 404, когда страница не найдена.'
            )
