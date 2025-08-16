# cv_app/models.py
from django.db import models
from django.contrib.auth.models import User

class CVTemplate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='cv_templates/')
    template_file = models.CharField(max_length=100)  # Name of the template file

    def __str__(self):
        return self.name

class CV(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(CVTemplate, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Personal Information
    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    
    # Professional Summary
    professional_summary = models.TextField(blank=True)
    
    # Key Skills
    key_skills = models.TextField(blank=True)
    
    # Work Experience (could also be a separate model for multiple entries)
    work_experience = models.TextField(blank=True)
    
    # Education
    education = models.TextField(blank=True)
    
    # Additional Sections
    certifications = models.TextField(blank=True)
    languages = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    
    # References
    references = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s CV ({self.template.name})"