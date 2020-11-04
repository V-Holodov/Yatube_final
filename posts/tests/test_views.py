from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class StaticViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()

    def create_post(self, title, slug, text):
        """auxiliary method for creating a test post and group"""
        username = self.user.username
        new_group = Group.objects.create(
            title=title,
            slug=slug
            )
        group_id = new_group.id
        new_post = Post.objects.create(
            text=text,
            author=self.user,
            group=new_group
            )
        post_id = new_post.id
        return {
            'username': username,
            'new_group': new_group,
            'new_post': new_post,
            'group_id': group_id,
            'post_id': post_id
            }

    def check_pages(self, username, post_id, slug, text, text_error):
        """auxiliary method for checks on the required pages"""
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': username}),
            reverse('post', kwargs={'username': username, 'post_id': post_id}),
            reverse('group_posts', kwargs={'slug': slug}),
        ]
        for url in urls:
            request_client = [
                self.authorized_client.get(url),
                self.unauthorized_client.get(url)
                ]
            for response in request_client:
                self.assertContains(
                    response,
                    text,
                    msg_prefix=text_error
                    )

    def test_new_post(self):
        """checks whether a post can be added and saved in the database"""
        current_posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('new_post'), {'text': 'Это текст публикации'}, follow=True
            )
        self.assertEqual(
            response.status_code,
            200,
            'Функция добавления нового поста работает неправильно'
            )
        self.assertEqual(
            Post.objects.count(),
            current_posts_count + 1,
            'Новый пост не сохраняется в базе данных'
            )

    def test_new_profile(self):
        """checking the creation of a user profile after registration"""
        username = self.user.username
        response = self.unauthorized_client.get(
            reverse('profile', kwargs={'username': username})
            )
        self.assertEqual(
            response.status_code,
            200,
            'Профайл пользователя не создается после регистрации'
            )

    def test_show_new_post(self):
        """checks whether an new post exists on the required pages """
        title = 'Тестовая группа',
        slug = 'testgroup'
        text = 'Это текст публикации'
        dict = self.create_post(title=title, slug=slug, text=text)
        cache.clear()
        self.check_pages(
            username=dict['username'],
            post_id=dict['post_id'],
            slug=slug,
            text=text,
            text_error='Новый пост не отображается на требуемых страницах'
            )

    def test_show_edit_post(self):
        """checks whether an edited post exists on the required pages"""
        title = 'Тестовая группа',
        slug = 'testgroup'
        text = 'Это текст публикации'
        dict = self.create_post(title=title, slug=slug, text=text)
        another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='anothergroup'
            )
        another_group_id = another_group.id
        edit_post = self.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': dict['username'],
                    'post_id': dict['post_id']
                    }
                ),
                    {
                        'text': 'Это отредактированный текст',
                        'group': another_group_id
                        },
            follow=True
            )
        cache.clear()
        self.check_pages(
            username=dict['username'],
            post_id=dict['post_id'],
            slug='anothergroup',
            text='Это отредактированный текст',
            text_error='Отредактированный пост не отображается на страницах'
            )
        self.assertNotContains(
            self.authorized_client.get(
                reverse('group_posts', kwargs={'slug': slug})
                ),
            'Это текст публикации',
            msg_prefix='Пост не исчез со страницы исходной группы'
            )

    def test_image(self):
        """checking whether the image is displayed correctly in the template"""
        title = 'Тестовая группа',
        slug = 'testgroup'
        text = 'Это текст публикации'
        dict = self.create_post(title=title, slug=slug, text=text)

        with open('media/media/imagetest.jpeg', 'rb') as img:
            edit_post = self.authorized_client.post(
                reverse(
                    'post_edit',
                    kwargs={
                        'username': dict['username'],
                        'post_id': dict['post_id']}
                    ),
                    {
                        'text': 'post with image',
                        'group': dict['group_id'],
                        'image': img
                        },
                follow=True
            )
        cache.clear()
        self.check_pages(
            username=dict['username'],
            post_id=dict['post_id'],
            slug=slug,
            text="<img",
            text_error='Картинка не отображается правильно'
            )

    def test_image_not_graphic_format(self):
        """checking the availability of uploading images in a non-graphic format"""
        title = 'Тестовая группа',
        slug = 'testgroup'
        text = 'Это текст публикации'
        dict = self.create_post(title=title, slug=slug, text=text)
        with open('media/media/test.txt', 'rb') as img:
            edit_post = self.authorized_client.post(
                reverse(
                    'post_edit',
                    kwargs={
                        'username': dict['username'],
                        'post_id': dict['post_id']
                        }
                    ),

                    {
                        'text': 'post with image',
                        'group': dict['group_id'],
                        'image': img
                        },
                follow=True
            )
        cache.clear()
        self.assertNotContains(
                self.authorized_client.get('/'),
                "<img",
                msg_prefix='Защита от загрузки файлов не-графических форматов не работает'
                )

    def test_cache(self):
        """checks the cache operation"""
        post = self.authorized_client.post(
            reverse('new_post'), {'text': 'Это текст публикации'}, follow=True
            )
        self.assertNotContains(
                self.authorized_client.get('/'),
                'Это текст публикации',
                msg_prefix='Кэш не работает'
                )
        cache.clear()
        self.assertContains(
                self.authorized_client.get('/'),
                'Это текст публикации',
                msg_prefix='Кэш работает не правильно'
                )
