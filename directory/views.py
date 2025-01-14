from django.shortcuts import render, get_object_or_404
from .models import Business
from django.shortcuts import render
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from .models import Business, Category
from django.shortcuts import render, redirect
from .forms import BusinessForm  # You'll need to create this form
from .models import Business

def add_business(request):
    if request.method == 'POST':
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            # Assign the owner only if the user is authenticated
            if request.user.is_authenticated:
                business.owner = request.user
            else:
                business.owner = None  # Set owner to None for anonymous users
            business.save()
            return redirect('business-detail', pk=business.pk)
    else:
        form = BusinessForm()
    return render(request, 'directory/add_business.html', {'form': form})


from django.db.models import Q

def business_list(request):
    # Get search query, category filter, and sort_by parameter from the request
    query = request.GET.get('q')
    category = request.GET.get('category')
    sort_by = request.GET.get('sort_by')

    # Start with all businesses and annotate with average rating and review count
    businesses = Business.objects.annotate(
        average_rating=Avg('reviews__rating'),  # Calculate average rating
        review_count=Count('reviews')           # Count reviews
    )

    # Apply search filter
    if query:
        businesses = businesses.filter(
            Q(name__icontains=query) |          # Search in name
            Q(description__icontains=query) |   # Search in description
            Q(address__icontains=query) |       # Search in address
            Q(tags__name__icontains=query)      # Search in tags (if using django-taggit)
        ).distinct()  # Use distinct() to avoid duplicate results

    # Apply category filter
    if category:
        businesses = businesses.filter(category__name__icontains=category)

    # Apply sorting based on the sort_by parameter
    if sort_by == 'rating':
        businesses = businesses.order_by('-average_rating')  # Sort by average rating (highest to lowest)
    elif sort_by == 'name':
        businesses = businesses.order_by('name')  # Sort by name (A-Z)
    elif sort_by == 'reviews':
        businesses = businesses.order_by('-review_count')  # Sort by most reviewed
    elif sort_by == 'newest':
        businesses = businesses.order_by('-created_at')  # Sort by newest (most recent first)
    else:
        # Default sorting: newest first
        businesses = businesses.order_by('-created_at')  # Newest businesses appear first by default

    # Paginate the results (10 businesses per page)
    paginator = Paginator(businesses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all categories for the filter dropdown
    categories = Category.objects.all()

    # Render the template with the paginated results, categories, and other context variables
    return render(request, 'directory/business_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category,
        'sort_by': sort_by,  # Pass the selected sort_by value to the template
    })

from django.shortcuts import render, get_object_or_404
from .models import Business, Review, Category
from .forms import ReviewForm
from django.contrib import messages

def business_detail(request, pk):
    business = get_object_or_404(Business, pk=pk)
    related_businesses = Business.objects.filter(category=business.category).exclude(pk=pk)[:5]
    reviews = Review.objects.filter(business=business, status='approved')  # Only show approved reviews

    # Paginate reviews
    paginator = Paginator(reviews, 5)  # Show 5 reviews per page
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.business = business

            if request.user.is_authenticated:
                review.user = request.user
            else:
                session_key = request.session.session_key
                if not session_key:
                    request.session.save()
                    session_key = request.session.session_key
                review.session_key = session_key

            review.save()
            messages.success(request, 'Your review has been submitted and is pending approval.')
            return redirect('business-detail', pk=pk)
    else:
        form = ReviewForm()

    return render(request, 'directory/business_detail.html', {
        'business': business,
        'related_businesses': related_businesses,
        'reviews': reviews,
        'form': form,
    })

from django.shortcuts import render, redirect, get_object_or_404
from .models import Business
from .forms import BusinessImageForm

def upload_business_image(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    if request.method == 'POST':
        form = BusinessImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.business = business
            image.save()
            return redirect('business_detail', business_id=business.id)
    else:
        form = BusinessImageForm()
    return render(request, 'upload_image.html', {'form': form, 'business': business})

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def privacy(request):
    return render(request, 'privacy.html')

def terms(request):
    return render(request, 'terms.html')