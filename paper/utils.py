from django.utils.text import slugify
import uuid

def generate_unique_slug(name):
    slug = slugify(name)  # Convert the name to a slug
    unique_slug = slug
    while Guest.objects.filter(slug=unique_slug).exists():  # Ensure uniqueness
        unique_slug = f"{slug}-{uuid.uuid4().hex[:6]}"  # Append a unique identifier
    return unique_slug