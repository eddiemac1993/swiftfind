# swiftfind/celery.py
from celery import Celery

app = Celery('swiftfind')
app.conf.beat_schedule = {
    'delete-old-posts': {
        'task': 'posts.tasks.delete_old_posts',
        'schedule': 30.0,  # Runs every 30 seconds (for testing)
    },
}