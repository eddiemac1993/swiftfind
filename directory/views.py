from django.shortcuts import render, get_object_or_404
from .models import Business
from django.shortcuts import render
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from .models import Business, Category
from django.shortcuts import render, redirect
from .forms import BusinessForm
from .models import Business
from django.utils import timezone
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')  # Redirect to the home page or any other page
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Business, Category
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm, ProfileUpdateForm, BusinessUpdateForm
from .models import Category

@login_required
def profile(request):
    user = request.user
    profile = user.profile
    business = profile.business

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        business_form = BusinessUpdateForm(request.POST, request.FILES, instance=business)

        if user_form.is_valid() and profile_form.is_valid() and business_form.is_valid():
            user_form.save()
            profile_form.save()
            business_form.save()
            return redirect('profile')  # Redirect to the profile page after saving
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)
        business_form = BusinessUpdateForm(instance=business)

    categories = Category.objects.all()
    return render(request, 'registration/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'business_form': business_form,
        'categories': categories,
    })

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


from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.shortcuts import render
from .models import SearchQuery, Business, Category, Advertisement
import random

def business_list(request):
    query = request.GET.get('q')
    city = request.GET.get('city', '')
    category = request.GET.get('category')
    sort_by = request.GET.get('sort_by')

    # Log search query if applicable
    if query or city or category or sort_by:
        search_query, created = SearchQuery.objects.get_or_create(
            query=query,
            city=city,
            category=category,
            sort_by=sort_by,
            defaults={'timestamp': timezone.now()}
        )
        if not created:
            search_query.count += 1
            search_query.save()

    # Annotate businesses with ratings and review counts
    businesses = Business.objects.annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews'),
        comment_count=Count('reviews', filter=Q(reviews__comment__isnull=False) & ~Q(reviews__comment=""))
    )

    # Apply filters based on query, city, and category
    if query:
        businesses = businesses.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    if city:
        businesses = businesses.filter(city__icontains=city)

    if category:
        businesses = businesses.filter(category__name__icontains=category)

    # Apply sorting
    if sort_by == 'rating':
        businesses = businesses.order_by('-average_rating')
    elif sort_by == 'name':
        businesses = businesses.order_by('name')
    elif sort_by == 'reviews':
        businesses = businesses.order_by('-review_count')
    elif sort_by == 'newest':
        businesses = list(businesses)  # Convert queryset to list
        random.shuffle(businesses)  # Shuffle the list
    else:
        businesses = businesses.order_by('?')

    # Fetch active advertisements
    now = timezone.now()
    active_ads = Advertisement.objects.filter(
        start_time__lte=now,  # Advertisements that have started
        end_time__gte=now,    # Advertisements that have not ended
        is_active=True        # Advertisements that are active
    )

    # Combine businesses and advertisements
    combined_list = []
    ad_index = 0
    interval = 5  # Show an ad after every 5 businesses

    for i, business in enumerate(businesses, start=1):
        combined_list.append(('business', business))  # Add business to the list

        # Add an ad after every `interval` businesses
        if i % interval == 0 and active_ads.exists():
            ad = active_ads[ad_index % len(active_ads)]  # Cycle through ads
            combined_list.append(('advertisement', ad))
            ad_index += 1

    # Paginate the combined list
    paginator = Paginator(combined_list, 100)  # Adjust page size as needed
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Count businesses on the current page
    businesses_count_on_page = len([item for item in page_obj.object_list if item[0] == 'business'])

    # Fetch all categories for the sidebar/filter
    categories = Category.objects.all()

    return render(request, 'directory/business_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'city': city,
        'selected_category': category,
        'sort_by': sort_by,
        'businesses_count_on_page': businesses_count_on_page,
    })


from django.shortcuts import render, get_object_or_404
from .models import Business, Review, Category
from .forms import ReviewForm
from django.contrib import messages

def business_detail(request, pk):
    business = get_object_or_404(Business, pk=pk)
    related_businesses = Business.objects.filter(category=business.category).exclude(pk=pk)[:5]
    reviews = Review.objects.filter(business=business, status='pending')  # Only show approved reviews

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