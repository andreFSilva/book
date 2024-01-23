from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
    TrigramSimilarity,
)


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)  # 3 posts in each page
    page = request.GET.get("page")
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    return render(
        request, "blog/post/list.html", {"page": page, "posts": posts, "tag": tag}
    )


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        slug=post,
        status="published",
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )
    # Lista dos comentários ativos para esta postagem
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == "POST":
        # Um comentário foi postado
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Cria o objeto Comment, mas não o salva inda no banco de dados
            new_comment = comment_form.save(commit=False)
            # Atribui a postagem atual ao comentário.
            new_comment.post = post
            # Salva o comentário no banco de dados.
            new_comment.save()
    else:
        comment_form = CommentForm()

    # Lista de postagens semelhantes
    post_tags_ids = post.tags.values_list("id", flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count("tags")).order_by(
        "-same_tags", "-publish"
    )[:4]
    return render(
        request,
        "blog/post/detail.html",
        {
            "post": post,
            "comments": comments,
            "new_comment": new_comment,
            "comment_form": comment_form,
            "similar_posts": similar_posts,
        },
    )


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = "posts"
    paginate_by = 3
    template_name = "blog/post/list.html"


"""def post_share(request, post_id):
    # Obtém a postgam com base no id
    post = get_object_or_404(Post, id=post_id, status='published')

    if request.method == 'POST':
        # Formulário foi submetido
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Campos do formulário passaram pela validação
            cd = form.cleaned_data
            #...envia o email
        else:
            form = EmailPostForm()
        return render(request, 'blog/post/share.html', {'post': post, 'form': form})"""


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status="published")
    sent = False  # Se enviado...
    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']}recommends you read{post.title}"
            message = f"REad{post.title} at {post_url}\n\n{cd['name']}comments: {cd['comments']}"
            send_mail(subject, message, "andrealekhine@gmail.com", [cd["to"]])
            sent = True  # Se enviado...
    else:
        form = EmailPostForm()
    return render(
        request, "blog/post/share.html", {"post": post, "form": form, "sent": sent}
    )


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if "query" in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            results = (
                Post.published.annotate(
                    similarity=TrigramSimilarity("title", query),
                )
                .filter(similarity__gt=0.1)
                .order_by("-similarity")
            )
    return render(
        request,
        "blog/post/search.html",
        {"form": form, "query": query, "results": results},
    )
