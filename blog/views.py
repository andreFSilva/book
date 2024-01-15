from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from .models import Post
from django.views.generic import ListView
from .forms import EmailPostForm
from django.core.mail import send_mail


def post_list(request):
    object_list = Post.published.all()
    paginator = Paginator(object_list, 3) # três postagens em cada página
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger: # se a pagina não for um inteiro, exibe a primeria página
        posts = paginator.page(1)
    except EmptyPage: # se a página for maior que o total de páginas, exibe a última página
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'posts': posts})

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status='published',
                             publish__year=year, publish__month=month,
                             publish__day=day)
    return render(request,'blog/post/detail.html', {'post': post})

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

'''def post_share(request, post_id):
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
        return render(request, 'blog/post/share.html', {'post': post, 'form': form})'''
def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False # Se enviado...
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']}recommends you read{post.title}"
            message = f"REad{post.title} at {post_url}\n\n{cd['name']}comments: {cd['comments']}"
            send_mail(subject, message, 'andrealekhine@gmail.com', [cd['to']])
            sent = True # Se enviado...
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})


