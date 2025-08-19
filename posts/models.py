from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.urls import reverse
from enum import Enum
from django.utils import timezone
from django.contrib.auth import get_user_model
User = get_user_model()

class CategoryChoices(Enum):
    SERVICE = 'service'
    RENT = 'rent'
    JOB = 'job'

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name.replace('_', ' ').title()) for choice in cls]

CATEGORY_CHOICES = CategoryChoices.choices()

class Post(models.Model):
    title = models.CharField(max_length=255, verbose_name="Post Title", help_text="Enter a descriptive title for your post.")
    slug = models.SlugField(unique=True, blank=True)
    business = models.ForeignKey(
        'directory.Business',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='postss',
        verbose_name="Associated Business",
        help_text="Select if this post is associated with a business"
    )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    description = models.TextField(verbose_name="Post Description", help_text="Provide details about the post.")
    category = models.CharField(max_length=15, choices=CATEGORY_CHOICES, verbose_name="Category", help_text="Select the category for the post.")
    phone_number = models.CharField(max_length=15, verbose_name="Phone Number", help_text="Enter your contact phone number.", default="0000000000")
    views = models.PositiveIntegerField(default=0, db_index=True, verbose_name="Views")
    votes = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Votes")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Created At")
    location = models.CharField(max_length=255, blank=True, verbose_name="Location", help_text="Enter the location relevant to the post.")
    price_range = models.CharField(max_length=100, blank=True, verbose_name="Price Range", help_text="Enter the price range if applicable.")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def has_business(self):
        return self.business is not None

    def save(self, *args, **kwargs):
        # Check if this is an existing post being updated
        if self.pk:
            original_post = Post.objects.get(pk=self.pk)

            # Delete if post is older than 1 week (7 days)
            if timezone.now() - original_post.created_at > timedelta(weeks=1):
                self.delete()
                return  # Exit without saving

        # Normal save operation for new posts or recent posts
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.slug)])

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name.title()) for choice in cls]

# models.py
# models.py
from django.conf import settings
from django.contrib.auth import get_user_model

class Comment(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']  # Newest first by default

    def __str__(self):
        return f"Comment by {self.user.username if self.user else 'Anonymous'} on {self.post.title}"