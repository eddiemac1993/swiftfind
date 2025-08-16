from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from taggit.managers import TaggableManager
from django.db.models import Avg
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth.hashers import make_password
from django.db.models import Q


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
    content = CKEditor5Field(config_name='default')
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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return f"Comment on {self.newsfeed.title}"

class Advertisement(models.Model):
    SLOT_CHOICES = [(i, f'Slot {i}') for i in range(1, 11)]

    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='advertisements/')
    link = models.URLField(blank=True, null=True)
    small_text = models.CharField(max_length=100, default="Paid Advert")
    slot = models.IntegerField(choices=SLOT_CHOICES, unique=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (Slot {self.slot})"

    def is_running(self):
        now = timezone.now()
        # Handle None values safely
        if not hasattr(self, 'start_time') or not hasattr(self, 'end_time'):
            return False
        if self.start_time is None or self.end_time is None:
            return False
        return self.start_time <= now <= self.end_time and self.is_active

    def days_remaining(self):
        if self.end_time is None:
            return None
        delta = self.end_time - timezone.now()
        return max(delta.days, 0)  # Returns 0 if already expired

    class Meta:
        ordering = ['slot']

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class BusinessRole(models.Model):
    """
    Defines roles within a business (e.g., Teacher, Student, Manager, Employee)
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text="Specific permissions for this role",
        related_name="business_roles"
    )
    is_default = models.BooleanField(default=False, help_text="Is this a default role for new members?")

    def __str__(self):
        return self.name

class BusinessDepartment(models.Model):
    """
    Organizational units within a business (e.g., Math Department, HR Department)
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent_department = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Business(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=False, blank=True)
    logo = models.ImageField(
        upload_to='business_logos/',
        default='business_logos/default.jpg',
        blank=True,
        null=True
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_businesses', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = CKEditor5Field(config_name='default')
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='businesses_referred')
    referral_fee_paid = models.BooleanField(default=False)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    is_admin_added = models.BooleanField(default=False, verbose_name="Verified Status")
    verified_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Verification End Date",
        help_text="Date until which this business remains verified"
    )
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    tags = TaggableManager(blank=True)
    company_profile = models.FileField(
        upload_to='company_profiles/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        blank=True,
        null=True,
        help_text="Upload a PDF file. Max size: 5MB"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    default_roles = models.ManyToManyField(BusinessRole, blank=True, related_name='default_businesses')
    departments = models.ManyToManyField(BusinessDepartment, blank=True, related_name='businesses')
    show_store_link = models.BooleanField(
        default=True,
        verbose_name="Show Store Link",
        help_text="Toggle to show/hide the store link in navigation"
    )

    @property
    def is_verified(self):
        """Check if business is currently verified (both flag is true and date is in future)"""
        if not self.is_admin_added:
            return False
        if self.verified_until:
            return timezone.now() <= self.verified_until
        return True

    @property
    def verification_days_left(self):
        """Return number of days left for verification or None if not verified"""
        if self.is_verified and self.verified_until:
            delta = self.verified_until - timezone.now()
            return delta.days
        return None

    def clean(self):
        super().clean()
        if self.company_profile:
            if self.company_profile.size > 5 * 1024 * 1024:
                raise ValidationError({'company_profile': "File size must be under 5MB."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
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

    @classmethod
    def search(cls, query=None, city=None, category=None):
        queryset = cls.objects.filter(status='active')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__name__in=[query])
            ).distinct()
        if city:
            queryset = queryset.filter(city__iexact=city)
        if category:
            queryset = queryset.filter(category__name__iexact=category)
        return queryset

class BusinessMember(models.Model):
    """
    Represents a user's membership in a business with specific credentials and role
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_memberships')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='members')
    role = models.ForeignKey(BusinessRole, on_delete=models.SET_NULL, null=True, blank=True)

    # Business-specific credentials
    business_username = models.CharField(max_length=150, unique=True)
    business_password = models.CharField(max_length=128)

    # Status fields
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Additional business-specific profile
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    department = models.ForeignKey(BusinessDepartment, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('user', 'business')

    def __str__(self):
        return f"{self.user.username} at {self.business.name} as {self.role.name if self.role else 'No Role'}"

    def set_password(self, raw_password):
        self.business_password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.business_password)

class BusinessPost(models.Model):
    POST_TYPE_CHOICES = [
        ('product', 'Product'),
        ('service', 'Service'),
        ('announcement', 'Announcement'),
        ('offer', 'Special Offer'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = CKEditor5Field('text')
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='product')
    image = models.ImageField(upload_to='business_posts/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.business.name}"

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
        unique_together = ('business', 'session_key')

    def save(self, *args, **kwargs):
        # Generate slug if not exists
        if not self.slug:
            self.slug = slugify(f"{self.business.name}-{timezone.now().strftime('%Y%m%d%H%M%S')}")

        # Set session key if user is anonymous
        if not self.user and not self.session_key:
            self.session_key = self._get_session_key()

        super().save(*args, **kwargs)

    def _get_session_key(self):
        from django.contrib.sessions.backends.db import SessionStore
        session = SessionStore()
        session.create()
        return session.session_key

    def __str__(self):
        return f"Review for {self.business.name}"

class BusinessImage(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='business_images/', blank=True, null=True)
    thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFill(200, 200)],
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
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_name = models.CharField(max_length=100)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name}: {self.message[:50]}"

class SearchQuery(models.Model):
    query = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    sort_by = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    count = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.query} - {self.timestamp} (Count: {self.count})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    receive_message_emails = models.BooleanField(
        default=True,
        verbose_name="Receive message notifications via email"
    )
    receive_notification_emails = models.BooleanField(
        default=True,
        verbose_name="Receive general notifications via email"
    )
    receive_marketing_emails = models.BooleanField(
        default=True,
        verbose_name="Receive marketing emails"
    )
    primary_business = models.ForeignKey(Business, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_employees')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Add this method to the User model
User.add_to_class('get_profile', lambda user: UserProfile.objects.get_or_create(user=user)[0])

class Referral(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_received')
    referred_business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='referrals',
        null=True,  # Make this optional
        blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=5.50)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('referred_user', 'referred_business')

    def __str__(self):
        return f"{self.referrer} → {self.referred_user}"
