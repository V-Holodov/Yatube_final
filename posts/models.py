from django.db import models
from django.contrib.auth import get_user_model
from .validators import validate_not_empty

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=70, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Поле обязательно для ввода текста'
        validators=[validate_not_empty]
        )
    pub_date = models.DateTimeField(
        "date published",
        auto_now_add=True,
        db_index=True
        )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="posts"
        )
    group = models.ForeignKey(
        verbose_name='Группа',
        Group, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name="posts",
        help_text='Выбирите группу'
        )
    image = models.ImageField(
        verbose_name='Картинка',
        help_text='Загрузите картинку',
        upload_to='posts/',
        blank=True, null=True
        )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text


class Comment(models.Model):

    """comment linked to the post and author"""

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name="comments"
        )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="comments"
        )
    text = models.TextField(validators=[validate_not_empty])
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return self.text


class Follow(models.Model):

    """the follow system on the author"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
                )
        ]
