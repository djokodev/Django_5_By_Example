from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.views.generic import ListView

from taggit.models import Tag

from .forms import EmailPostForm, CommentForm
from .models import Post, Comment



@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED
    )
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(False)
        comment.post = post
        comment.save()
    return render(
        request,
        'blog/post/comment.html',
        {
            'post': post,
            'form': form,
            'comment': comment
        }
    )

def post_share(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED
    )

    sent = False

    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            # Puisque nous devons inclure un lien vers l'article dans l'e-mail, nous récupérons le chemin absolu de l'article en utilisant sa méthode get_absolute_url().
            # Nous utilisons ce chemin comme entrée pour request.build_absolute_uri() afin de construire une URL complète, incluant le schéma HTTP et le nom d'hôte.
            post_url = request.build_absolute_uri(
                post.get_absolute_url()
            )

            subject = (
                f"{cd['name']} ({cd['email']})"
                f"recommends you read {post.title}"
            )
            message = (
                f"Read {post.title} at {post_url}\n\n"
                f"{cd['name']}\'s comments: {cd['comments']}"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[cd['to']]
            )

            sent = True
    else:
        form = EmailPostForm()
    return render(
        request,
        'blog/post/share.html',
        {
            'post': post,
            'form': form,
            'sent': sent
        }
    )


# class PostListView(ListView):
#     "Alternative post_list view"
#
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.html'

def post_list(request, tag_slug=None):
    post_list = Post.published.all()

    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    paginator = Paginator(post_list, 3)

    # Savoir quelle page l'utilisateur veut voir : L'utilisateur communique son choix via l'URL.
    # http://.../blog/ -> Il ne précise rien, on suppose qu'il veut la page 1.
    # http://.../blog/?page=2 -> Il demande explicitement la page 2.
    # On récupère cette information depuis la requête HTTP
    page_number = request.GET.get('page', 1)

    try:
        # Elle ne renvoie PAS une simple liste de 3 articles. Elle renvoie un objet spécial "Page".
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        # Si l'utilisateur a demandé une page qui n'existe pas (trop grande), on lui donne la toute dernière page (posts = paginator.page(paginator.num_pages)).
        # C'est plus sympa que de lui afficher une erreur
        posts = paginator.page(paginator.num_pages)
    return render(
        request,
        'blog/post/list.html',
        {
            'posts':posts,
            'tag': tag
        }
    )

def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day
    )
    # try:
    #     post = Post.published.get(id=id)
    # except Post.DoesNotExist:
    #     raise Http404("No Post found")

    # Liste des commentaires actif pour cette article
    comments = post.comments.filter(active=True)

    form = CommentForm()

    return render(
        request,
        'blog/post/detail.html',
        {
            'post': post,
            'comments':comments,
            'form': form
        }
    )