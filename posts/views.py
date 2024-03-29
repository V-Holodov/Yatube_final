from django import forms
from django.http import request
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


@cache_page(1 * 20, key_prefix="index_page")
def index(request):
    """home page with a list of posts"""
    latest = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(latest, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {"page": page, "paginator": paginator}
        )


def group_posts(request, slug):
    """group page with a list of posts"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, "page": page, "paginator": paginator}
        )


@login_required
def new_post(request):
    """creating a new post by an authorized user"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('index')
    return render(request, 'new_post.html', {'form': form, 'edit': False})


def profile(request, username):
    """displaying the user's profile page with their posts,
    the number of followers and following
    """
    user = request.user
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follower = author.follower.count()
    following = author.following.count()
    if request.user.is_authenticated is True:
        follow = Follow.objects.filter(author=author, user=user).exists()
    else:
        follow = ''
    return render(
        request,
        'profile.html',
        {
            'author': author,
            'posts': posts,
            'paginator': paginator,
            'page': page,
            'follower': follower,
            'following': following,
            'follow': follow
            }
        )


def post_view(request, username, post_id):
    """displaying a post, comment form, and list of comments"""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    follower = author.follower.count()
    following = author.following.count()
    comments = Comment.objects.select_related('author', 'post').filter(post_id=post_id)
    form = CommentForm()
    return render(
        request,
        'post.html',
        {
            'author': author,
            'post': post,
            'comments': comments,
            'form': form,
            'follower': follower,
            'following': following,
            'item': True
            }
        )


@login_required
def post_edit(request, username, post_id):
    """edits the text, group, or image for a post"""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=post.author.username, post_id=post.id)
    return render(
        request,
        'new_post.html',
        {'form': form, 'post': post, 'edit': True}
        )


def page_not_found(request, exception):
    """overrides page 404"""
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    """overrides page 500"""
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    """adds a new comment to the post"""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    """the display of the ribbon with the tracked records of the authors"""
    user = request.user
    latest = Post.objects.filter(author__following__user=user)
    paginator = Paginator(latest, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page, "paginator": paginator})


@login_required
def profile_follow(request, username):
    """starts following the author if it is not the user himself"""
    user = request.user
    author = User.objects.get(username=username)
    if author != user:
        follow = Follow.objects.get_or_create(author=author, user=user)
    return redirect('profile', username=username)


@login_required
@cache_page(1 * 20, key_prefix="index_page")
def profile_unfollow(request, username):
    """stops following the author"""
    user = request.user
    follow = Follow.objects.filter(author__username=username, user=user)
    follow.delete()
    return redirect('profile', username=username)


@login_required
def post_delete(request, username, post_id):
    """delete a post"""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    post.delete()
    return redirect('index')


@login_required
def comment_delete(request, username, post_id, author_comment, comment_id):
    """delete a comment"""
    comment = get_object_or_404(Comment, author__username=author_comment, id=comment_id)
    comment.delete()
    messages.success(request, 'Profile updated successfully')
    return redirect('post', username=username, post_id=post_id)


def search_post(request):
    """Search for a post by the content of the 'text' field"""
    search_query = request.GET.get('search_query')
    if search_query != "":
        latest = Post.objects.order_by("-pub_date").filter(text__icontains=search_query)
        if latest.exists():
            paginator = Paginator(latest, 20)
            page_number = request.GET.get('page')
            page = paginator.get_page(page_number)
            return render(
                request,
                "search_results.html",
                {"page": page, "paginator": paginator, "search": True}
                )
        else:
            return render(
                request,
                "search_results.html",
                {"text": "По Вашему запросу ничего не найдено.", "search": False}
                )
    else:
        return render(
            request,
            "search_results.html",
            {"text": "Пустой запрос", "search": False}
            )
