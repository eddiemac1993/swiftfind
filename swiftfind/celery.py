# swiftfind/celery.py
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swiftfind.settings')

app = Celery('swiftfind')

# Load task modules from all registered Django apps
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Schedule for beat
app.conf.beat_schedule = {
    'delete-old-posts': {
        'task': 'posts.tasks.delete_old_posts',
        'schedule': 30.0,  # Every 30 secs (for testing)
    },
}