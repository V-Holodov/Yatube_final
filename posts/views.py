from django import forms

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


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
    form = PostForm(request.POST or None)
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
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follower = author.follower.count()
    following = author.following.count()
    return render(
        request,
        'profile.html',
        {
            'author': author,
            'posts': posts,
            'paginator': paginator,
            'page': page,
            'follower': follower,
            'following': following
            }
        )


def post_view(request, username, post_id):
    """displaying a message, comment form, and list of comments"""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    comments = Comment.objects.select_related('author', 'post').filter(post_id=post_id)
    form = CommentForm()
    return render(
        request,
        'post.html',
        {
            'author': author,
            'post': post,
            'comments': comments,
            'form': form
            }
        )


@login_required
def post_edit(request, username, post_id):
    """edits the text, group, or image for a post"""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(request.POST  or None, files=request.FILES or None, instance=post)
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
    user_follow = Follow.objects.filter(user=user)
    authors = User.objects.filter(following__in=user_follow)
    latest = Post.objects.filter(author__in=authors)
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
def profile_unfollow(request, username):
    """stops following the author"""
    user = request.user
    author = User.objects.get(username=username)
    follow = Follow.objects.filter(author=author, user=user)
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
    return redirect('post', username=username, post_id=post_id)
