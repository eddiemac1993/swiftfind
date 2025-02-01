from django.shortcuts import render, get_object_or_404
from .models import Business
from django.shortcuts import render
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from .models import Business, Category
from django.shortcuts import render, redirect
from .forms import BusinessForm  # You'll need to create this form
from .models import Business
from django.utils import timezone

from django.shortcuts import render

def offline(request):
    return render(request, 'offline.html')

def add_business(request):
    if request.method == 'POST':
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            if request.user.is_authenticated:
                business.owner = request.user
                # Check if the user is an admin
                if request.user.is_staff or request.user.is_superuser:
                    business.is_admin_added = True
            else:
                business.owner = None
            business.save()
            return redirect('business-detail', pk=business.pk)
    else:
        form = BusinessForm()
    return render(request, 'directory/add_business.html', {'form': form})


from django.db.models import Q
from .models import SearchQuery  # Import the SearchQuery model

from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.shortcuts import render
from .models import SearchQuery, Business, Category  # Import your models

def business_list(request):
    # Get search query, category filter, and sort_by parameter from the request
    query = request.GET.get('q')
    city = request.GET.get('city', '')
    category = request.GET.get('category')
    sort_by = request.GET.get('sort_by')

    # Log the search query if a query or filter is provided
    if query or city or category or sort_by:
        # Check if an identical search query already exists
        search_query, created = SearchQuery.objects.get_or_create(
            query=query,
            city=city,
            category=category,
            sort_by=sort_by,
            defaults={'timestamp': timezone.now()}  # Set the timestamp for new queries
        )

        # If the query already exists, increment the count
        if not created:
            search_query.count += 1
            search_query.save()

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

    if city:
        businesses = businesses.filter(city__icontains=city)

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

    # Get the number of businesses on the current page
    businesses_count_on_page = len(page_obj.object_list)

    # Get all categories for the filter dropdown
    categories = Category.objects.all()

    # Render the template with the paginated results, categories, and other context variables
    return render(request, 'directory/business_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'city': city,
        'selected_category': category,
        'sort_by': sort_by,  # Pass the selected sort_by value to the template
        'businesses_count_on_page': businesses_count_on_page,  # Pass the count of businesses on the current page
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

from django.http import JsonResponse
from .models import ChatRoom, ChatMessage
from .utils import get_client_ip, generate_random_name

# List all chat rooms
def chat_room_list(request):
    rooms = ChatRoom.objects.all().order_by('-created_at')
    return render(request, 'chat/room_list.html', {'rooms': rooms})

# Create a new chat room
def create_chat_room(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            ChatRoom.objects.create(name=name, description=description)
            return redirect('chat_room_list')
    return render(request, 'chat/create_room.html')

# View for a specific chat room
def chat_room_detail(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    return render(request, 'chat/chat_room_detail.html', {'room': room})

# Handle sending messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import ChatRoom, ChatMessage
from .utils import get_client_ip, generate_random_name

def send_message(request, room_id):
    if request.method == 'POST':
        # Retrieve the chat room
        room = get_object_or_404(ChatRoom, id=room_id)

        # Get the message from the request
        message = request.POST.get('message')
        if not message:
            return JsonResponse({'status': 'error', 'message': 'Message is required'}, status=400)

        # Get the user's IP address
        ip_address = get_client_ip(request)

        # Generate a random name based on the IP address
        user_name = generate_random_name(ip_address)

        # Create the ChatMessage instance
        ChatMessage.objects.create(
            room=room,
            message=message,
            user_name=user_name,
            ip_address=ip_address,
        )

        return JsonResponse({'status': 'success', 'message': 'Message sent successfully'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)