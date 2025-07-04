from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.urls import reverse
from enum import Enum

class CategoryChoices(Enum):
    SERVICE = 'service'
    RENT = 'rent'

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name.replace('_', ' ').title()) for choice in cls]

CATEGORY_CHOICES = CategoryChoices.choices()

class Post(models.Model):
    title = models.CharField(max_length=255, verbose_name="Post Title", help_text="Enter a descriptive title for your post.")
    slug = models.SlugField(unique=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.slug)])

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name.title()) for choice in cls]

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    name = models.CharField(max_length=100, verbose_name="Name", help_text="Enter your name or username.", default="Anonymous")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"