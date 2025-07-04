from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from .models import Post, Comment, CategoryChoices
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import PostForm  # Ensure you have a form for post creation

class PostCreateView(CreateView):
    model = Post
    form_class = PostForm  # Use a Django ModelForm for the post
    template_name = 'posts/post_form.html'  # Ensure this template exists
    success_url = reverse_lazy('post_list')

# List posts with brief description
def post_list(request):
    category = request.GET.get('category')
    posts = Post.objects.annotate(comment_count=Count('comments')).order_by('-created_at')

    if category:
        posts = posts.filter(category=category)

    category_choices = [(choice.value, choice.name.title()) for choice in CategoryChoices]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'posts/post_list_partial.html', {
            'posts': posts,
            'category_choices': category_choices
        })

    return render(request, 'posts/post_list.html', {
        'posts': posts,
        'category_choices': category_choices
    })

# Detailed view with full description, voting, and comments
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.views += 1
    post.save()

    if request.method == "POST":
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        parent = Comment.objects.get(id=parent_id) if parent_id else None
        Comment.objects.create(post=post, content=content, parent=parent)

    comments = post.comments.filter(parent=None)
    return render(request, 'posts/post_detail.html', {'post': post, 'comments': comments})

# Voting system (Upvote / Downvote)
def vote_post(request, post_id, vote_type):
    post = get_object_or_404(Post, id=post_id)
    post.votes += 1 if vote_type == "up" else -1
    post.save()
    return redirect('post_detail', post_id=post.id)
