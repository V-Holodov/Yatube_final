from django.test import TestCase
from posts.models import Post


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Post.objects.create(
            text='Текст',
            group=''
            )
