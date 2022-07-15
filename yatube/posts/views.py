from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import pagination


# Кэш перенесен в темплейт
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related(
        'group', 'author').all()
    page_obj = pagination(request, posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group.objects.prefetch_related('posts__author'), slug=slug)
    posts = group.posts.all()
    page_obj = pagination(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User.objects.prefetch_related('posts','following','follower'), username=username)
    posts = author.posts.all()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    page_obj = pagination(request, posts)
    context = {
        'author': author,
        'posts': posts,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post.objects.select_related('author','group'), pk=post_id)
    author = post.author
    comments = post.comments.all()
    form = CommentForm()

    context = {
        'post': post,
        'author': author,
        'comments': comments,
        'form': form

    }
    return render(request, template, context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            data=request.POST or None,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(
                'posts:profile',
                post.author
            )
        return render(
            request,
            'posts/create_post.html',
            {'form': form}
        )

    form = PostForm()
    return render(
        request,
        'posts/create_post.html',
        {'form': form}
    )


# Описал ситуацию в слаке
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if post.author != request.user:
        return redirect('posts:post', post_id)
    if request.method == 'POST':
        form = PostForm(
            instance=post,
            data=request.POST or None,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=True)
            post.save()
            return redirect('posts:post', post_id)
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': is_edit, 'post': post}
        )
    form = PostForm(instance=post)
    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'is_edit': is_edit, 'post': post}
    )


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, id=post_id)
        comment.save()
    return redirect('posts:post', post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    posts = Post.objects.select_related(
        'group', 'author').filter(author__following__user=request.user)
    page_obj = pagination(request, posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = User.objects.get(username=username)
    follow_check = not Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    # Проверка для исключения 500й ошибки у шаловливых ручек
    if request.user != author and follow_check:
        Follow.objects.create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(author=author).exists()
    # Проверка для исключения 500й ошибки у шаловливых ручек
    if request.user != author and follow_check:
        Follow.objects.filter(
            user=request.user,
            author=author
        ).delete()
    return redirect('posts:profile', author)


