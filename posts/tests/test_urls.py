from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()

    def test_homepage(self):
        """main page request test"""
        response = self.unauthorized_client.get('/')
        self.assertEqual(
            response.status_code,
            200,
            'Главная страница не доступна'
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
