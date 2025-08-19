# posts/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Post

@shared_task
def delete_old_posts():
    # TEST: Change `weeks=1` to `minutes=1` for quick testing
    time_threshold = timezone.now() - timedelta(minutes=1)  
    
    old_posts = Post.objects.filter(created_at__lt=time_threshold)
    count = old_posts.count()
    old_posts.delete()
    print(f"[Celery Task] Deleted {count} old posts")  # Check Celery logs for this