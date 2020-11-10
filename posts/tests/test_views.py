from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from PIL import Image
import os
import tempfile

from posts.models import Post, Group

User = get_user_model()


class StaticViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.author = User.objects.create_user(username='IvanIvanov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.author)
        cls.title = 'Тестовая группа',
        cls.slug = 'testgroup'
        cls.text = 'Это текст публикации'
        cls.new_group = Group.objects.create(
            title=cls.title,
            slug=cls.slug
            )
        cls.new_post = Post.objects.create(
            text=cls.text,
            author=cls.user,
            group=cls.new_group)

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
        cache.clear()
        self.check_pages(
            username=self.user.username,
            post_id=self.new_post.id,
            slug=self.slug,
            text=self.text,
            text_error='Новый пост не отображается на требуемых страницах'
            )

    def test_show_edit_post(self):
        """checks whether an edited post exists on the required pages"""
        another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='anothergroup'
            )
        another_group_id = another_group.id
        edit_post = self.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.new_post.id
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
            username=self.user.username,
            post_id=self.new_post.id,
            slug='anothergroup',
            text='Это отредактированный текст',
            text_error='Отредактированный пост не отображается на страницах'
            )
        self.assertNotContains(
            self.authorized_client.get(
                reverse('group_posts', kwargs={'slug': self.slug})
                ),
            'Это текст публикации',
            msg_prefix='Пост не исчез со страницы исходной группы'
            )

    def test_image(self):
        """checking whether the image is displayed correctly in the template"""
        img = Image.new("RGB", (100, 100))
        img.save('img.png')
        with open('img.png', 'rb') as img:
            self.authorized_client.post(
                reverse(
                    'post_edit',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.new_post.id}
                    ),
                    {
                        'text': 'post with image',
                        'group': self.new_group.id,
                        'image': img
                        },
                follow=True
                )
        cache.clear()
        self.check_pages(
            username=self.user.username,
            post_id=self.new_post.id,
            slug=self.slug,
            text="<img",
            text_error='Картинка не отображается правильно'
            )
        os.remove('img.png')

    def test_image_not_graphic_format(self):
        """the availability of uploading images in a non-graphic format"""
        with tempfile.TemporaryFile(mode='w+b', suffix='.txt') as img:
            img.write(b'Hello world!')
            img.seek(0)
            edit_post = self.authorized_client.post(
                reverse(
                    'post_edit',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.new_post.id
                        }
                    ),
                    {
                        'text': 'post with image',
                        'group': self.new_group.id,
                        'image': img
                        },
                follow=True
                )
            cache.clear()
            self.assertNotContains(
                self.authorized_client.get(reverse('index')),
                "<img",
                msg_prefix='Защита от загрузки неизображений не работает'
                )
            self.assertFormError(
                edit_post,
                'form',
                'image',
                'Upload a valid image. The file you uploaded was either not an image or a corrupted image.',
                'Поле "image" в форме не выдает ошибок при загрузки не изображений'
                )
        img.close()

    def test_cache(self):
        """checks the cache operation"""
        self.authorized_client.post(
            reverse('new_post'), {'text': 'Это тест кэша'}, follow=True
            )
        self.assertNotContains(
                self.authorized_client.get(reverse('index')),
                'Это тест кэша',
                msg_prefix='Кэш не работает'
                )
        cache.clear()
        self.assertContains(
                self.authorized_client.get(reverse('index')),
                'Это текст публикации',
                msg_prefix='Кэш работает не правильно'
                )

    def test_follow(self):
        """operation of the 'follow' system"""
        following_user = self.user.follower.count()
        author = self.author.username
        self.authorized_client.get(
            reverse("profile_follow", kwargs={'username': author})
            )
        self.assertEqual(
            self.user.follower.count(),
            following_user + 1,
            'Функция подписки работает неправильно'
            )

    def test_follow_post(self):
        """displaying a post in the subscription feed"""
        author = self.author.username
        self.authorized_client.get(
            reverse("profile_follow", kwargs={'username': author})
            )
        post = self.authorized_client2.post(
            reverse('new_post'), {'text': 'Текст автора'}, follow=True
        )
        cache.clear()
        self.assertContains(
            self.authorized_client.get(reverse("follow_index")),
            'Текст автора',
            msg_prefix='Пост автора не появляется у подписчиков в ленте'
        )

    def test_unfollow(self):
        """operation of the 'unfollow' system"""
        author = self.author.username
        self.authorized_client.get(
            reverse("profile_follow", kwargs={'username': author})
            )
        following_user = self.user.follower.count()
        self.authorized_client.get(
            reverse("profile_unfollow", kwargs={'username': author})
            )
        self.assertEqual(
            self.user.follower.count(),
            following_user - 1,
            'Функция отписки работает неправильно')

    def test_unfollow_post(self):
        """displaying a post in the subscription feed after unfollow"""
        author = self.author.username
        self.authorized_client.get(
            reverse("profile_follow", kwargs={'username': author})
            )
        post = self.authorized_client2.post(
            reverse('new_post'), {'text': 'Текст автора'}, follow=True
        )
        self.authorized_client.get(
            reverse("profile_unfollow", kwargs={'username': author})
            )
        cache.clear()
        self.assertNotContains(
            self.authorized_client.get(reverse("follow_index")),
            'Текст автора',
            msg_prefix='Пост автора появляется не только у подписчиков'
        )

    def test_comment_authorized_user(self):
        """adding comments to authorized users"""
        post = Post.objects.create(text='Текст поста', author=self.user)
        self.authorized_client.post(
            reverse(
                'add_comment',
                kwargs={'username': self.user, 'post_id': post.id}
                ),
            {'text': 'Текст авторизованного пользователя'}
        )
        self.assertContains(
            self.authorized_client.get(
                reverse(
                    'post',
                    kwargs={'username': self.user, 'post_id': post.id}
                    ),
                ),
            'Текст авторизованного пользователя',
            msg_prefix='авторизованный user не может оставить комментарий'
        )

    def test_comment_unauthorized_user(self):
        """adding comments to unauthorized users"""
        post = Post.objects.create(text='Текст поста', author=self.user)
        self.unauthorized_client.post(
            reverse(
                'add_comment',
                kwargs={'username': self.user, 'post_id': post.id}
                ),
            {'text': 'Текст неавторизованного пользователя'}
        )
        self.assertNotContains(
            self.authorized_client.get(
                reverse(
                    'post',
                    kwargs={'username': self.user, 'post_id': post.id}
                    ),
                ),
            'Текст неавторизованного пользователя',
            msg_prefix='Комментарии доступны незарегистрированным пользователю'
        )
