from django.contrib import admin
from .models import Category, Business, Review, BusinessImage
from django import forms
from django.contrib import admin
from django import forms
from django.contrib import admin
from django.utils.text import slugify
from django.shortcuts import redirect
from .models import Category

class MultipleCategoryForm(forms.Form):
    names = forms.CharField(
        widget=forms.Textarea,
        help_text="Enter one category per line.",
        required=False  # Make this field optional
    )

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    add_form_template = 'admin/directory/category_add_form.html'  # Use the custom template

    def add_view(self, request, form_url='', extra_context=None):
        if request.method == 'POST':
            # Check if the bulk creation form was submitted
            if 'names' in request.POST:
                form = MultipleCategoryForm(request.POST)
                if form.is_valid():
                    names = form.cleaned_data['names'].splitlines()
                    for name in names:
                        name = name.strip()
                        if name:
                            slug = slugify(name)
                            counter = 1
                            while Category.objects.filter(slug=slug).exists():
                                slug = f"{slugify(name)}-{counter}"
                                counter += 1
                            Category.objects.create(name=name, slug=slug)
                    self.message_user(request, f"Added {len(names)} categories.")
                    # Redirect to the category list page after bulk creation
                    return redirect('admin:directory_category_changelist')
            else:
                # Handle the default single category creation form
                return super().add_view(request, form_url, extra_context)
        else:
            form = MultipleCategoryForm()

        extra_context = extra_context or {}
        extra_context['form'] = form
        return super().add_view(request, form_url, extra_context)

admin.site.register(Category, CategoryAdmin)

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'address', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'address', 'owner__username')
    raw_id_fields = ('owner', 'category')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('business', 'rating', 'title', 'status', 'created_at')
    list_filter = ('status', 'rating', 'created_at')
    search_fields = ('business__name', 'title', 'comment')
    list_editable = ('status',)
    raw_id_fields = ('business', 'user')
    date_hierarchy = 'created_at'

@admin.register(BusinessImage)
class BusinessImageAdmin(admin.ModelAdmin):
    list_display = ['business', 'image', 'caption', 'created_at']
    list_filter = ['business']
    search_fields = ['business__name', 'caption']