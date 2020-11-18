from django.test import TestCase, Client
from django.urls.base import reverse
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site


class StaticURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()

    def test_about_author(self):
        """checking page 'about author' availability"""
        flatpage = FlatPage.objects.create(
            url='/about-author/',
            title='author',
            )
        flatpage.sites.set([1])
        response = self.client.get(reverse('about-author'))
        self.assertEqual(
            response.status_code,
            200,
            'Страница "Об авторе" не доступна'
            )

    def test_about_spec(self):
        """checking page 'about spec' availability"""
        flatpage = FlatPage.objects.create(
            url='/about-spec/',
            title='spec',
            )
        flatpage.sites.set([1])
        response = self.client.get(reverse('about-spec'))
        self.assertEqual(
            response.status_code,
            200,
            'Страница "Технологии" не доступна'
            )
