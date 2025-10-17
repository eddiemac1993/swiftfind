# Standard library imports
from random import shuffle

# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login as auth_login
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.models import Permission

# Local imports
from .models import (
    Business,
    Category,
    Review,
    SearchQuery,
    Advertisement,
    NewsFeed,
    Comment,
    UserProfile,
    BusinessPost,
    ChatRoom,
    ChatMessage,
    BusinessMember,
    BusinessRole,
    BusinessDepartment
)
from .forms import (
    BusinessForm,
    BusinessUpdateForm,
    ReviewForm,
    CommentForm,
    UserRegistrationForm,
    UserUpdateForm,
    ProfileUpdateForm,
    BusinessPostForm,
    BusinessImageForm,
    BusinessMemberForm,
    BusinessRoleForm,
    BusinessDepartmentForm
)
from .utils import get_client_ip, generate_random_name
from .auth_backends import BusinessAuthBackend

# directory/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from datetime import timedelta
from .models import Business

@permission_required('directory.can_verify', raise_exception=True)
def update_business_verification(request, business_id):
    business = get_object_or_404(Business, id=business_id)

    if request.method == 'POST':
        if 'verify_business' in request.POST:
            verification_status = request.POST.get('verification_status')
            verification_notes = request.POST.get('verification_notes', '')

            # Update verification based on selection
            if verification_status == 'unverified':
                business.is_admin_added = False
                business.verified_until = None
            elif verification_status == '30_days':
                business.is_admin_added = True
                business.verified_until = timezone.now() + timedelta(days=30)
            elif verification_status == '90_days':
                business.is_admin_added = True
                business.verified_until = timezone.now() + timedelta(days=90)
            elif verification_status == 'permanent':
                business.is_admin_added = True
                business.verified_until = None

            # Record who verified this business
            business.verified_by = request.user
            business.verification_date = timezone.now()
            business.save()

            messages.success(request, f"Business verification updated successfully.")

        elif 'unverify_business' in request.POST:
            business.is_admin_added = False
            business.verified_until = None
            business.verified_by = None
            business.verification_date = None
            business.save()

            messages.success(request, "Business verification removed.")

    return redirect('directory:business_profile', business_id=business.id)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required
from directory.models import Business
from django.utils import timezone
from datetime import timedelta
# directory/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import permission_required
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import permission_required
from .models import Business

@permission_required('directory.can_verify', raise_exception=True)
def business_verification_dashboard(request):
    businesses = Business.objects.all().order_by('verified_until')

    if request.method == "POST":
        business_id = request.POST.get('business_id')
        business = Business.objects.get(id=business_id)

        # Automatically verify for 30 days
        business.is_admin_added = True
        business.verified_until = timezone.now() + timedelta(days=30)
        business.verified_by = request.user
        business.verification_date = timezone.now()
        business.save()

        messages.success(request, f"{business.name} has been verified for 30 days.")
        return redirect('business_verification_dashboard')

    context = {'businesses': businesses}
    return render(request, 'directory/business_verification_dashboard.html', context)


@permission_required('directory.can_verify', raise_exception=True)
def business_verification_list(request):
    # Show all businesses except those already permanently verified (optional)
    businesses = Business.objects.filter(is_admin_added=False) | Business.objects.filter(verified_until__lt=timezone.now())
    businesses = businesses.order_by('-created_at')

    context = {
        'businesses': businesses,
    }
    return render(request, 'directory/business_verification_list.html', context)

@login_required
def products_list(request):
    # Get all products from all businesses
    products = BusinessPost.objects.all().select_related('business').order_by('-created_at')

    # Get distinct businesses for filters
    all_businesses = Business.objects.filter(
        id__in=products.values_list('business_id', flat=True).distinct()
    ).order_by('name')

    # Apply filters
    search_query = request.GET.get('q')
    selected_business = request.GET.get('business')
    sort_by = request.GET.get('sort', 'newest')

    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(business__name__icontains=search_query)
        )

    if selected_business:
        products = products.filter(business_id=selected_business)

    # Apply sorting
    if sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.annotate(
            review_count=Count('reviews')
        ).order_by('-review_count', '-created_at')
    elif sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'directory/products_list.html', {
        'products': page_obj,
        'all_businesses': all_businesses,
        'search_query': search_query,
        'selected_business': selected_business,
        'sort_by': sort_by,
    })

@login_required
def add_product(request):
    business = Business.objects.filter(owner=request.user).first()
    if not business:
        messages.warning(request, "You don't have a business profile yet.")
        return redirect('profile')

    if request.method == 'POST':
        form = BusinessPostForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.business = business
            product.save()
            messages.success(request, 'Product/Service added successfully!')
            return redirect('products-list')
    else:
        form = BusinessPostForm()

    return render(request, 'directory/add_product.html', {
        'form': form,
        'business': business
    })

@login_required
def edit_product(request, pk):
    product = get_object_or_404(BusinessPost, pk=pk)

    # Check if the product belongs to the user's business
    if product.business.owner != request.user:
        messages.error(request, "You don't have permission to edit this item.")
        return redirect('products-list')

    if request.method == 'POST':
        form = BusinessPostForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product/Service updated successfully!')
            return redirect('products-list')
    else:
        form = BusinessPostForm(instance=product)

    return render(request, 'directory/edit_product.html', {
        'form': form,
        'product': product
    })

@login_required
def delete_product(request, pk):
    product = get_object_or_404(BusinessPost, pk=pk)

    # Check if the product belongs to the user's business
    if product.business.owner != request.user:
        messages.error(request, "You don't have permission to delete this item.")
        return redirect('products-list')

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product/Service deleted successfully!')
        return redirect('products-list')

    return render(request, 'directory/delete_product.html', {
        'product': product
    })

from django.db.models import Count, Q

def all_products(request):
    # Get all active products
    products = BusinessPost.objects.filter().select_related('business')

    # Get distinct businesses and categories for filters
    all_businesses = Business.objects.filter(
        id__in=products.values_list('business_id', flat=True).distinct()
    ).order_by('name')

    all_categories = Category.objects.filter(
        id__in=products.values_list().distinct()
    ).order_by('name')

    # Apply filters
    search_query = request.GET.get('q')
    selected_business = request.GET.get('business')
    selected_category = request.GET.get('category')
    selected_type = request.GET.get('type')
    sort_by = request.GET.get('sort', 'newest')

    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(business__name__icontains=search_query)
        )

    if selected_business:
        products = products.filter(business_id=selected_business)

    if selected_category:
        products = products.filter(category_id=selected_category)

    if selected_type:
        products = products.filter(post_type=selected_type)

    # Apply sorting
    if sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.annotate(
            review_count=Count('reviews')
        ).order_by('-review_count', '-created_at')
    elif sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'directory/all_products.html', {
        'products': page_obj,
        'all_businesses': all_businesses,
        'all_categories': all_categories,
        'search_query': search_query,
        'selected_business': selected_business,
        'selected_category': selected_category,
        'selected_type': selected_type,
        'sort_by': sort_by,
    })

def product_detail(request, business_id, product_id):
    product = get_object_or_404(BusinessPost, pk=product_id, business__id=business_id)

    related_products = BusinessPost.objects.filter(
        business=product.business
    ).exclude(pk=product.id).order_by('?')[:4]

    return render(request, 'directory/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'business': product.business
    })
# Helper functions
def handle_review_submission(request, business):
    review_form = ReviewForm(request.POST)
    if review_form.is_valid():
        review = review_form.save(commit=False)
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
        return redirect('business-detail', pk=business.pk)

    # If form is invalid, we'll return to the view with the invalid form
    return None

def handle_post_submission(request, business, pk):
    post_form = BusinessPostForm(request.POST, request.FILES)
    if post_form.is_valid():
        post = post_form.save(commit=False)
        post.business = business

        # Set default values if needed
        if not post.price:
            post.price = None  # Explicitly set to None if empty

        post.save()

        # Handle image separately if needed
        if 'image' in request.FILES:
            # Additional image processing could go here
            pass

        messages.success(request, 'Your post has been added successfully!')
        return redirect('business-detail', pk=pk)

    # If form is invalid, we'll return to the view with the invalid form
    return None

def paginate_queryset(request, queryset, page_param, per_page):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get(page_param)
    return paginator.get_page(page_number)

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
        shuffle(businesses)  # Shuffle the list
    else:
        businesses = businesses.order_by('?')

    # Fetch active advertisements
    now = timezone.now()
    active_ads = Advertisement.objects.filter(
        start_time__lte=now,
        end_time__gte=now,
        is_active=True
    )

    # Fetch newsfeeds
    newsfeeds = NewsFeed.objects.all().order_by('-created_at')[:5]

    # Combine businesses, advertisements, and newsfeeds
    combined_list = []
    ad_index = 0
    newsfeed_index = 0
    interval = 5  # Show an ad after every 5 businesses
    newsfeed_interval = 2  # Show a newsfeed after every 2 businesses

    for i, business in enumerate(businesses, start=1):
        combined_list.append(('business', business))

        # Add a newsfeed after every `newsfeed_interval` businesses
        if i % newsfeed_interval == 0 and newsfeed_index < len(newsfeeds):
            combined_list.append(('newsfeed', newsfeeds[newsfeed_index]))
            newsfeed_index += 1

        # Add an ad after every `interval` businesses
        if i % interval == 0 and active_ads.exists():
            ad = active_ads[ad_index % len(active_ads)]  # Cycle through ads
            combined_list.append(('advertisement', ad))
            ad_index += 1

    # Paginate the combined list
    paginator = Paginator(combined_list, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Count businesses on the current page
    businesses_count = businesses.count()
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
        'businesses_count': businesses_count,
    })

@login_required
def add_business_post(request, pk):
    business = get_object_or_404(Business, pk=pk)

    # Check if user has permission to post for this business
    if not (request.user == business.owner or
            request.user.is_staff or
            BusinessMember.objects.filter(user=request.user, business=business).exists()):
        return HttpResponseForbidden("You don't have permission to post for this business.")

    if request.method == 'POST':
        form = BusinessPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.business = business
            post.save()
            messages.success(request, "Your post has been added successfully!")
            return redirect('business-detail', pk=pk)
    else:
        form = BusinessPostForm()

    return render(request, 'directory/add_business_post.html', {
        'form': form,
        'business': business
    })

@login_required
def edit_business_post(request, pk):
    post = get_object_or_404(BusinessPost, pk=pk)
    business = post.business

    # Check if user has permission to edit this post
    if not (request.user == business.owner or
            request.user.is_staff or
            BusinessMember.objects.filter(user=request.user, business=business).exists()):
        return HttpResponseForbidden("You don't have permission to edit this post.")

    if request.method == 'POST':
        form = BusinessPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully!")
            return redirect('business-detail', pk=business.pk)
    else:
        form = BusinessPostForm(instance=post)

    return render(request, 'directory/edit_business_post.html', {
        'form': form,
        'post': post,
        'business': business
    })

@login_required
def delete_business_post(request, pk):
    post = get_object_or_404(BusinessPost, pk=pk)
    business = post.business

    # Check if user has permission to delete this post
    if not (request.user == business.owner or
            request.user.is_staff or
            BusinessMember.objects.filter(user=request.user, business=business).exists()):
        return HttpResponseForbidden("You don't have permission to delete this post.")

    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post deleted successfully!")
        return redirect('business-detail', pk=business.pk)

    return render(request, 'directory/delete_business_post.html', {
        'post': post,
        'business': business
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Avg
from django.contrib import messages
from pos_system.models import Product, ProductCategory
from .models import Business, Review, BusinessPost, BusinessMember
from .forms import ReviewForm, BusinessPostForm

def business_detail(request, pk):
    business = get_object_or_404(Business, pk=pk)
    related_businesses = Business.objects.filter(category=business.category).exclude(pk=pk)[:5]

    # Show only approved reviews
    reviews_qs = Review.objects.filter(business=business, status='approved').select_related('user')
    posts_qs = BusinessPost.objects.filter(business=business).order_by('-is_featured', '-created_at')

    # Add products query for the store section
    products_qs = Product.objects.filter(
        business=business,
        is_active=True,
        stock_quantity__gt=0
    ).select_related('category', 'business').order_by('?')

    product_categories = ProductCategory.objects.filter(
        product__in=products_qs
    ).distinct()

    review_count = reviews_qs.count()
    average_rating = reviews_qs.aggregate(Avg('rating'))['rating__avg'] or 0
    business.review_count = review_count
    business.average_rating = average_rating

    business_stats = {
        'review_count': review_count,
        'average_rating': average_rating,
    }

    is_member = is_owner_or_admin = False
    if request.user.is_authenticated:
        is_member = BusinessMember.objects.filter(user=request.user, business=business).exists()
        is_owner_or_admin = any([
            request.user == business.owner,
            request.user.is_staff,
            is_member
        ])

    if request.method == 'POST':
        if 'submit_review' in request.POST:
            rating = request.POST.get('rating')
            comment = request.POST.get('comment')
            if rating:
                try:
                    with transaction.atomic():
                        review = Review(
                            business=business,
                            rating=rating,
                            comment=comment,
                            status='pending'  # All reviews go through approval
                        )

                        if request.user.is_authenticated:
                            # Check if user already reviewed this business
                            if Review.objects.filter(business=business, user=request.user).exists():
                                messages.warning(request, 'You have already submitted a review for this business.')
                                return redirect('business-detail', pk=pk)
                            review.user = request.user
                        else:
                            # For anonymous users, use session key
                            session_key = request.session.session_key
                            if not session_key:
                                request.session.save()
                                session_key = request.session.session_key
                            review.session_key = session_key

                            # Check if session already reviewed this business
                            if Review.objects.filter(business=business, session_key=session_key).exists():
                                messages.warning(request, 'You have already submitted a review for this business.')
                                return redirect('business-detail', pk=pk)

                        review.save()
                        messages.success(request, 'Your review has been submitted and is pending approval.')
                        return redirect('business-detail', pk=pk)
                except Exception as e:
                    messages.error(request, f'An error occurred while submitting your review: {str(e)}')
                    return redirect('business-detail', pk=pk)

        elif 'submit_post' in request.POST and is_owner_or_admin:
            return handle_post_submission(request, business, pk)
        elif 'edit_post' in request.POST and is_owner_or_admin:
            return handle_post_edit(request, business, pk)
        elif 'delete_post' in request.POST and is_owner_or_admin:
            return handle_post_delete(request, business, pk)

    reviews = paginate_queryset(request, reviews_qs, 'review_page', 50)
    posts = paginate_queryset(request, posts_qs, 'post_page', 16)
    products = paginate_queryset(request, products_qs, 'product_page', 1000)

    review_form = ReviewForm()
    post_form = BusinessPostForm() if is_owner_or_admin else None

    context = {
        'business': business,
        'related_businesses': related_businesses,
        'reviews': reviews,
        'posts': posts,
        'products': products,
        'product_categories': product_categories,
        'review_form': review_form,
        'post_form': post_form,
        'is_owner_or_admin': is_owner_or_admin,
        'is_member': is_member,
        'business_stats': business_stats,
        'is_store_section': request.path.endswith('/store/'),  # Flag to identify store section
    }

    # Use different templates for store vs detail view if you prefer
    template_name = 'pos_system/public_store.html' if request.path.endswith('/store/') else 'directory/business_detail.html'
    return render(request, template_name, context)

def handle_post_edit(request, business, pk):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(BusinessPost, id=post_id, business=business)
    post_form = BusinessPostForm(request.POST, request.FILES, instance=post)

    if post_form.is_valid():
        post_form.save()
        messages.success(request, 'Post updated successfully!')
    else:
        messages.error(request, 'Error updating post. Please check the form.')

    return redirect('business-detail', pk=pk)

def handle_post_delete(request, business, pk):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(BusinessPost, id=post_id, business=business)
    post.delete()
    messages.success(request, 'Post deleted successfully!')
    return redirect('business-detail', pk=pk)

from .models import Category  # Import your Category model
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ReferralForm
from .models import Referral

@login_required
@login_required
def add_business(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        business_form = BusinessForm(request.POST, request.FILES)
        referral_form = ReferralForm(request.POST)

        if business_form.is_valid() and referral_form.is_valid():
            try:
                with transaction.atomic():
                    business = business_form.save(commit=False)
                    business.owner = request.user

                    # Check if user was referred by someone
                    user_referral = Referral.objects.filter(referred_user=request.user).first()
                    if user_referral:
                        business.referred_by = user_referral.referrer

                    # Handle direct business referral if provided
                    referrer = referral_form.cleaned_data.get('referrer_username')
                    if referrer:
                        business.referred_by = referrer
                        Referral.objects.create(
                            referrer=referrer,
                            referred_user=request.user,
                            referred_business=business,
                            amount=2.50
                        )
                        messages.info(request, f"Thank you for using {referrer.username}'s referral!")

                    business.save()
                    business_form.save_m2m()
                    messages.success(request, 'Business created successfully!')
                    return redirect('profile')

            except Exception as e:
                messages.error(request, f'Error creating business: {str(e)}')
        else:
            for field, errors in business_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            for field, errors in referral_form.errors.items():
                for error in errors:
                    messages.error(request, f"Referral: {error}")
    else:
        referral_username = request.GET.get('ref')
        initial = {'referrer_username': referral_username} if referral_username else {}
        business_form = BusinessForm()
        referral_form = ReferralForm(initial=initial)

    return render(request, 'directory/add_business.html', {
        'form': business_form,
        'referral_form': referral_form,
        'categories': categories
    })

from django.urls import reverse
from django.db.models import Sum

@login_required
def referral_dashboard(request):
    # Get all referrals where user is the referrer
    referrals_made = Referral.objects.filter(
        Q(referrer=request.user) |
        Q(referred_business__owner=request.user)
    ).select_related('referred_user', 'referred_business').distinct()

    referrals_made = Referral.objects.filter(referrer=request.user).select_related('referred_business', 'referred_user')
    total_earned = referrals_made.aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid = referrals_made.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    pending_payment = total_earned - total_paid

    # Generate a unique referral link
    referral_link = request.build_absolute_uri(
        reverse('register') + f"?ref={request.user.username}"
    )

    return render(request, 'referrals/dashboard.html', {
        'referrals_made': referrals_made,
        'total_earned': total_earned,
        'total_paid': total_paid,
        'pending_payment': pending_payment,
        'referral_link': referral_link,
    })

def upload_business_image(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    if request.method == 'POST':
        form = BusinessImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.business = business
            image.save()
            return redirect('business-detail', pk=business.id)
    else:
        form = BusinessImageForm()
    return render(request, 'upload_image.html', {'form': form, 'business': business})

def newsfeed_list(request):
    category = request.GET.get('category', None)
    newsfeed_items = NewsFeed.objects.all().order_by('-created_at')

    if category:
        newsfeed_items = newsfeed_items.filter(category=category)

    paginator = Paginator(newsfeed_items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'newsfeed_items': page_obj,
        'category_choices': NewsFeed.CATEGORY_CHOICES,
    }
    return render(request, 'directory/newsfeed_list.html', context)

def newsfeed_detail(request, pk):
    newsfeed = get_object_or_404(NewsFeed, pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.newsfeed = newsfeed
            if request.user.is_authenticated:
                comment.user = request.user
            comment.save()
            messages.success(request, 'Your comment has been posted!')
            return redirect('newsfeed_detail', pk=newsfeed.pk)
    else:
        form = CommentForm()

    comments = Comment.objects.filter(newsfeed=newsfeed, is_approved=True).order_by('-created_at')
    previous_newsfeed = NewsFeed.objects.filter(created_at__lt=newsfeed.created_at).order_by('-created_at').first()
    next_newsfeed = NewsFeed.objects.filter(created_at__gt=newsfeed.created_at).order_by('created_at').first()

    return render(request, 'directory/newsfeed_detail.html', {
        'newsfeed': newsfeed,
        'previous_newsfeed': previous_newsfeed,
        'next_newsfeed': next_newsfeed,
        'form': form,
        'comments': comments,
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import UserRegistrationForm, ReferralForm
from .models import UserProfile, Referral
from directory.models import Business  # Import your Business model if needed

from django.contrib.auth import get_user_model
User = get_user_model()
def register(request):
    registered_users = User.objects.all().order_by('username')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Handle referral if provided
            referrer_username = request.POST.get('referrer')
            if referrer_username:
                try:
                    referrer = User.objects.get(username=referrer_username)
                    user.save()  # Save user first to get an ID

                    # Create referral record
                    Referral.objects.create(
                        referrer=referrer,
                        referred_user=user,
                        amount=2.50
                    )
                    messages.success(request, f"Thanks for signing up through {referrer.username}'s referral!")
                except User.DoesNotExist:
                    messages.warning(request, "Invalid referral code. Proceeding with normal registration.")
                    user.save()
            else:
                user.save()

            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
        else:
            # Check for specific validation errors to provide better messages
            for field, errors in form.errors.items():
                for error in errors:
                    if 'email' in field.lower() and 'already' in error.lower():
                        messages.error(request, "This email is already registered. Please use a different email or try logging in.")
                    elif 'phone' in field.lower() and 'already' in error.lower():
                        messages.error(request, "This phone number is already registered. Please use a different phone number.")
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {
        'form': form,
        'registered_users': registered_users
    })

from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import UserProfile

def check_email(request):
    email = request.GET.get('email', '')
    exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({'exists': exists})

def check_phone(request):
    phone = request.GET.get('phone', '')
    exists = UserProfile.objects.filter(phone_number=phone).exists()
    return JsonResponse({'exists': exists})

@login_required
def profile(request):
    profile = request.user.profile
    business = Business.objects.filter(owner=request.user).first()

    # Calculate referral earnings
    referral_stats = {
        'total_earned': Referral.objects.filter(referrer=request.user).aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_paid': Referral.objects.filter(referrer=request.user, is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_payment': Referral.objects.filter(referrer=request.user, is_paid=False).aggregate(Sum('amount'))['amount__sum'] or 0,
    }

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        business_form = BusinessUpdateForm(request.POST, request.FILES, instance=business) if business else None

        if all(form.is_valid() for form in filter(None, [user_form, profile_form, business_form])):
            try:
                with transaction.atomic():
                    user_form.save()
                    profile_form.save()
                    if business_form:
                        business = business_form.save(commit=False)
                        business.show_store_link = business_form.cleaned_data.get('show_store_link', False)
                        business.save()
                        business_form.save_m2m()

                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
        business_form = BusinessUpdateForm(instance=business) if business else None

    context = {
        'user': request.user,
        'profile': profile,
        'user_form': user_form,
        'profile_form': profile_form,
        'business_form': business_form,
        'business': business,
        'has_business': business is not None,
        'referral_stats': referral_stats,  # Add referral stats to context
    }
    return render(request, 'registration/profile.html', context)

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.contrib import messages
import re

@login_required
def update_profile_phone(request):
    if request.method == "POST":
        phone_number = request.POST.get('phone_number', '').strip()

        # Optional: simple validation
        cleaned_phone = re.sub(r'[^\d+]', '', phone_number)
        if not re.match(r'^\+?\d{8,16}$', cleaned_phone):
            messages.error(request, "Enter a valid phone number including country code.")
            return redirect(request.META.get('HTTP_REFERER'))

        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.phone_number = cleaned_phone
        profile.save()
        messages.success(request, "Phone number updated successfully.")
    return redirect(request.META.get('HTTP_REFERER'))

def chat_room_list(request):
    rooms = ChatRoom.objects.all().order_by('-created_at')
    return render(request, 'chat/room_list.html', {'rooms': rooms})

def create_chat_room(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            ChatRoom.objects.create(name=name, description=description)
            return redirect('chat_room_list')
    return render(request, 'chat/create_room.html')

def chat_room_detail(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    return render(request, 'chat/chat_room_detail.html', {'room': room})

def send_message(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(ChatRoom, id=room_id)
        message = request.POST.get('message')
        if not message:
            return JsonResponse({'status': 'error', 'message': 'Message is required'}, status=400)

        ip_address = get_client_ip(request)
        user_name = generate_random_name(ip_address)

        ChatMessage.objects.create(
            room=room,
            message=message,
            user_name=user_name,
            ip_address=ip_address,
        )

        return JsonResponse({'status': 'success', 'message': 'Message sent successfully'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

# Business Management Views
@login_required
def business_dashboard(request, business_slug):
    business = get_object_or_404(Business, slug=business_slug)

    # Check if user is owner or member of this business
    if not (request.user == business.owner or
            BusinessMember.objects.filter(user=request.user, business=business).exists()):
        return HttpResponseForbidden("You don't have access to this business dashboard.")

    context = {
        'business': business,
        'members': business.members.all(),
        'departments': business.departments.all(),
        'roles': BusinessRole.objects.all(),
    }
    return render(request, 'business/dashboard.html', context)

@login_required
def add_business_member(request, business_slug):
    business = get_object_or_404(Business, slug=business_slug)

    # Check if user is owner or has permission to add members
    if not (request.user == business.owner or
            request.user.has_perm('directory.add_businessmember')):
        return HttpResponseForbidden("You don't have permission to add members.")

    if request.method == 'POST':
        form = BusinessMemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.business = business
            member.set_password(form.cleaned_data['password'])
            member.save()
            messages.success(request, 'Member added successfully')
            return redirect('business_dashboard', business_slug=business.slug)
    else:
        form = BusinessMemberForm()

    return render(request, 'business/add_member.html', {
        'form': form,
        'business': business,
        'roles': BusinessRole.objects.all()
    })

@login_required
def manage_roles(request, business_slug):
    business = get_object_or_404(Business, slug=business_slug)

    # Check if user is owner or has permission to manage roles
    if not (request.user == business.owner or
            request.user.has_perm('directory.manage_roles')):
        return HttpResponseForbidden("You don't have permission to manage roles.")

    if request.method == 'POST':
        form = BusinessRoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            messages.success(request, 'Role created successfully')
            return redirect('manage_roles', business_slug=business.slug)
    else:
        form = BusinessRoleForm()

    roles = BusinessRole.objects.all()
    return render(request, 'business/manage_roles.html', {
        'form': form,
        'roles': roles,
        'business': business,
        'permissions': Permission.objects.filter(content_type__model='business')
    })

@login_required
def manage_departments(request, business_slug):
    business = get_object_or_404(Business, slug=business_slug)

    # Check if user is owner or has permission to manage departments
    if not (request.user == business.owner or
            request.user.has_perm('directory.manage_departments')):
        return HttpResponseForbidden("You don't have permission to manage departments.")

    if request.method == 'POST':
        form = BusinessDepartmentForm(request.POST)
        if form.is_valid():
            department = form.save(commit=False)
            department.business = business
            department.save()
            messages.success(request, 'Department created successfully')
            return redirect('manage_departments', business_slug=business.slug)
    else:
        form = BusinessDepartmentForm()

    departments = business.departments.all()
    return render(request, 'business/manage_departments.html', {
        'form': form,
        'departments': departments,
        'business': business
    })

@login_required
def edit_business_member(request, business_slug, member_id):
    business = get_object_or_404(Business, slug=business_slug)
    member = get_object_or_404(BusinessMember, id=member_id, business=business)

    # Check if user is owner or has permission to edit members
    if not (request.user == business.owner or
            request.user.has_perm('directory.change_businessmember')):
        return HttpResponseForbidden("You don't have permission to edit members.")

    if request.method == 'POST':
        form = BusinessMemberForm(request.POST, instance=member)
        if form.is_valid():
            member = form.save()
            if form.cleaned_data['password']:
                member.set_password(form.cleaned_data['password'])
                member.save()
            messages.success(request, 'Member updated successfully')
            return redirect('business_dashboard', business_slug=business.slug)
    else:
        form = BusinessMemberForm(instance=member)

    return render(request, 'business/edit_member.html', {
        'form': form,
        'business': business,
        'member': member,
        'roles': BusinessRole.objects.all()
    })

@login_required
def delete_business_member(request, business_slug, member_id):
    business = get_object_or_404(Business, slug=business_slug)
    member = get_object_or_404(BusinessMember, id=member_id, business=business)

    # Check if user is owner or has permission to delete members
    if not (request.user == business.owner or
            request.user.has_perm('directory.delete_businessmember')):
        return HttpResponseForbidden("You don't have permission to delete members.")

    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Member deleted successfully')
        return redirect('business_dashboard', business_slug=business.slug)

    return render(request, 'business/delete_member.html', {
        'business': business,
        'member': member
    })

def business_login(request, business_slug):
    business = get_object_or_404(Business, slug=business_slug)

    if request.method == 'POST':
        business_username = request.POST.get('business_username')
        business_password = request.POST.get('business_password')

        backend = BusinessAuthBackend()
        user = backend.authenticate(
            request,
            business_username=business_username,
            business_password=business_password
        )

        if user is not None:
            auth_login(request, user, backend='yourapp.auth_backends.BusinessAuthBackend')
            # Update last login for the business member
            BusinessMember.objects.filter(
                user=user,
                business=business,
                business_username=business_username
            ).update(last_login=timezone.now())
            return redirect('business_dashboard', business_slug=business.slug)
        else:
            messages.error(request, 'Invalid business credentials')

    return render(request, 'business/login.html', {'business': business})

# Simple views
def become_partner(request):
    return render(request, 'directory/become_partner.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def privacy(request):
    return render(request, 'privacy.html')

def terms(request):
    return render(request, 'terms.html')

from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.utils.cache import patch_cache_control

@require_GET
def offline(request):
    """Enhanced offline view with proper caching headers"""
    response = render(request, 'offline.html')
    # Ensure the offline page itself isn't cached by browsers
    patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True)
    return response