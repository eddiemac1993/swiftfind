from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from taggit.managers import TaggableManager
from django.db.models import Avg
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure the slug is unique
            original_slug = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Business(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(
        upload_to='business_logos/',
        default='business_logos/default.jpg',
        blank=True,
        null=True
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='businesses', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    is_admin_added = models.BooleanField(default=False)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)  # New city field
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    tags = TaggableManager(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure the slug is unique
            original_slug = self.slug
            counter = 1
            while Business.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    def has_user_reviewed(self, user):
        if user.is_authenticated:
            return self.reviews.filter(user=user).exists()
        return False

    def __str__(self):
        return self.name

class Review(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=[(i, i) for i in range(1, 6)]
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    helpful_votes = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('business', 'session_key')  # Ensure one review per session per business

    def save(self, *args, **kwargs):
        if not self.slug:
            # Save the object first to get an ID
            super().save(*args, **kwargs)
            self.slug = slugify(f"{self.business.name}-{self.id}")
            # Save again to update the slug
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

        # Ensure session_key is set for anonymous users
        if not self.user and not self.session_key:
            self.session_key = self._get_session_key()
            super().save(*args, **kwargs)

    def _get_session_key(self):
        # Get or create a session key for anonymous users
        if not self.session_key:
            from django.contrib.sessions.backends.db import SessionStore
            session = SessionStore()
            session.create()
            return session.session_key
        return self.session_key

    def __str__(self):
        return f"Review for {self.business.name}"

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

class BusinessImage(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='business_images/', blank=True, null=True)
    thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFill(200, 200)],  # Resize to 200x200
        format='JPEG',
        options={'quality': 80}
    )
    caption = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image for {self.business.name}"

from django.db import models

class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # Store the user's IP address
    user_name = models.CharField(max_length=100)  # Store the random name
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name}: {self.message[:50]}"

from django.db import models
from django.utils import timezone

class SearchQuery(models.Model):
    query = models.CharField(max_length=255, blank=True, null=True)  # The search query
    city = models.CharField(max_length=100, blank=True, null=True)  # City filter
    category = models.CharField(max_length=100, blank=True, null=True)  # Category filter
    sort_by = models.CharField(max_length=50, blank=True, null=True)  # Sorting parameter
    timestamp = models.DateTimeField(default=timezone.now)  # When the search was performed
    count = models.PositiveIntegerField(default=1)  # Track the number of times this query has been performed

    def __str__(self):
        return f"{self.query} - {self.timestamp} (Count: {self.count})"