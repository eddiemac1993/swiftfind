from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from .models import Post, Comment, CategoryChoices
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import PostForm
from directory.models import Business
from messaging.models import Conversation

class PostCreateView(CreateView):
    model = Post
    form_class = PostForm  # Use a Django ModelForm for the post
    template_name = 'posts/post_form.html'  # Ensure this template exists
    success_url = reverse_lazy('post_list')

def post_list(request):
    category = request.GET.get('category')
    posts = Post.objects.select_related('business', 'author', 'author__profile').annotate(
        comment_count=Count('comments')
    ).order_by('-created_at')

    if category:
        posts = posts.filter(category=category)

    category_choices = [(choice.value, choice.name.title()) for choice in CategoryChoices]

    # Initialize notification counts
    unread_count = 0
    job_posts_count = 0

    if request.user.is_authenticated:
        try:
            unread_count = Conversation.objects.filter(
                participants=request.user,
                messages__read=False
            ).exclude(
                messages__sender=request.user
            ).distinct().count()
        except:
            unread_count = 0

        job_posts_count = Post.objects.filter(
            category='job',
        ).count()

    context = {
        'posts': posts,
        'category_choices': category_choices,
        'unread_count': unread_count,
        'job_notifications_count': job_posts_count,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'posts/post_list_partial.html', context)

    return render(request, 'posts/post_list.html', context)

from directory.models import Advertisement
from django.utils import timezone

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    business = None

    # Increment view count
    if not request.session.get(f'viewed_post_{post_id}'):
        post.views += 1
        post.save()
        request.session[f'viewed_post_{post_id}'] = True
        request.session.set_expiry(60 * 60 * 24)

    if post.author and hasattr(post.author, 'profile'):
        business = post.author.profile.primary_business

    if request.method == "POST" and request.user.is_authenticated:
        content = request.POST.get('content')
        if content:
            Comment.objects.create(
                post=post,
                user=request.user,
                content=content
            )
        return redirect('post_detail', post_id=post.id)

    # Get active advertisements
    now = timezone.now()
    active_ads = Advertisement.objects.filter(
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    ).order_by('slot')[:5]  # Get up to 5 active ads

    comments = post.comments.filter(parent=None).order_by('-created_at')
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'business': business,
        'active_ads': active_ads,
        'now': now
    })

# Voting system (Upvote / Downvote)
def vote_post(request, post_id, vote_type):
    post = get_object_or_404(Post, id=post_id)
    post.votes += 1 if vote_type == "up" else -1
    post.save()
    return redirect('post_detail', post_id=post.id)
