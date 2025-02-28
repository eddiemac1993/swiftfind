from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from taggit.managers import TaggableManager
from django.db.models import Avg
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.utils import timezone
from ckeditor.fields import RichTextField

class NewsFeed(models.Model):
    CATEGORY_CHOICES = [
        ('story', 'Story'),
        ('weather', 'Weather'),
        ('food', 'Food'),
        ('news', 'News'),
        ('event', 'Event'),
        ('sports', 'Sports'),
        ('over18', 'Over 18'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='news')
    content = RichTextField()
    image = models.ImageField(upload_to='newsfeed_images/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('newsfeed_detail', args=[str(self.id)])


class Comment(models.Model):
    newsfeed = models.ForeignKey('NewsFeed', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Optional: Track logged-in users
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return f"Comment on {self.newsfeed.title}"

class Advertisement(models.Model):
    SLOT_CHOICES = [(i, f'Slot {i}') for i in range(1, 11)]  # 10 slots

    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='advertisements/')
    link = models.URLField(blank=True, null=True)  # Link to redirect when the ad is clicked
    small_text = models.CharField(max_length=100, default="Paid Advert")  # Text to indicate it's an ad
    slot = models.IntegerField(choices=SLOT_CHOICES, unique=True)  # Unique slot number (1-10)
    start_time = models.DateTimeField()  # When the ad starts running
    end_time = models.DateTimeField()  # When the ad stops running
    is_active = models.BooleanField(default=True)  # To manually enable/disable the ad
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (Slot {self.slot})"

    def is_running(self):
        """Check if the ad is currently running based on the time."""
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.is_active

    class Meta:
        ordering = ['slot']

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
    description = RichTextField(blank=True, null=True)
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

class SearchQuery(models.Model):
    query = models.CharField(max_length=255, blank=True, null=True)  # The search query
    city = models.CharField(max_length=100, blank=True, null=True)  # City filter
    category = models.CharField(max_length=100, blank=True, null=True)  # Category filter
    sort_by = models.CharField(max_length=50, blank=True, null=True)  # Sorting parameter
    timestamp = models.DateTimeField(default=timezone.now)  # When the search was performed
    count = models.PositiveIntegerField(default=1)  # Track the number of times this query has been performed

    def __str__(self):
        return f"{self.query} - {self.timestamp} (Count: {self.count})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    business = models.ForeignKey(Business, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Add this method to the User model (or a custom user model)
User.add_to_class('get_profile', lambda user: UserProfile.objects.get_or_create(user=user)[0])