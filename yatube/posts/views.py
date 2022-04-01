from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.LIMIT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    posts = group.posts.all()
    paginator = Paginator(posts, settings.LIMIT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    template = 'posts/profile.html'
    post_list = Post.objects.filter(author__username=username)
    paginator = Paginator(post_list, settings.LIMIT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = Follow.objects.filter(
        author=author, user__username=request.user
    ).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'author_name': username,
        'count_user_post': post_list.count(),
        'following': following,
        'user': request.user,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    group = post.group
    author = post.author
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'group': group,
        'author': author,
        'form': form,
        'count_user_post': Post.objects.filter(author_id=post.author).count(),
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    is_edit = False
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user.username)
    context = {
        'form': form,
        'is_edit': is_edit,
    }
    return render(request, template, context)


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user:
        template = 'posts/create_post.html'
        is_edit = True
        form = PostForm(
            request.POST or None, instance=post,
            files=request.FILES or None,
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', pk)
        context = {
            'form': form,
            'is_edit': is_edit,
            'post': post,
        }
        return render(request, template, context)
    return redirect('posts:post_detail', pk)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.LIMIT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
