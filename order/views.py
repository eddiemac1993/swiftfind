from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Item, Cart, CartItem, ItemCategory
import json
from django.http import JsonResponse
from django.db.models import Exists, OuterRef
from django.shortcuts import render
from django.views import View
from directory.models import Business  # Assuming you have a Business model
from django.db.models import Avg, Count, Q
from django.utils import timezone
from directory.models import Advertisement
from directory.models import SearchQuery, Category, NewsFeed
from django.core.paginator import Paginator


def discover(request):
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

    # Fetch newsfeeds
    newsfeeds = NewsFeed.objects.all().order_by('-created_at')[:5]  # Adjust the number as needed

    # Combine businesses, advertisements, and newsfeeds
    combined_list = []
    ad_index = 0
    newsfeed_index = 0
    interval = 5  # Show an ad after every 5 businesses
    newsfeed_interval = 2  # Show a newsfeed after every 2 businesses

    for i, business in enumerate(businesses, start=1):
        combined_list.append(('business', business))  # Add business to the list

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
    paginator = Paginator(combined_list, 100)  # Adjust page size as needed
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Count businesses on the current page
    businesses_count = businesses.count()
    businesses_count_on_page = len([item for item in page_obj.object_list if item[0] == 'business'])

    # Fetch all categories for the sidebar/filter
    categories = Category.objects.all()

    return render(request, 'discover.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'city': city,
        'selected_category': category,
        'sort_by': sort_by,
        'businesses_count_on_page': businesses_count_on_page,
        'businesses_count': businesses_count,
    })

def get_cart(request):
    cart, created = Cart.objects.get_or_create(id=request.session.get('cart_id'))
    if created:
        request.session['cart_id'] = cart.id
    return cart


from django.db.models import Exists, OuterRef

def home(request):
    # Annotate each category with a boolean field 'has_items' indicating if it has any associated items
    categories = ItemCategory.objects.annotate(
        has_items=Exists(Item.objects.filter(category=OuterRef('id')))
    )

    items = Item.objects.all()
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category')

    if search_query:
        items = items.filter(name__icontains=search_query)

    if category_id:
        items = items.filter(category__id=category_id)

    # Get or create cart
    cart_id = request.session.get('cart_id')
    if cart_id:
        cart = Cart.objects.get(id=cart_id)
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    cart_count = sum(item.quantity for item in cart.cartitem_set.all())

    # Default hero section data
    hero_data = {
        'category_icon': 'fa-shopping-bag',  # Default icon
        'category_title': 'Di-Store',  # Default title
        'category_description': 'Your one-stop shop for quality products at affordable prices. Find everything you need for your projects.',  # Default description
    }

    # Update hero section data if a category is selected
    if category_id:
        try:
            selected_category = ItemCategory.objects.get(id=category_id)
            hero_data.update({
                'category_icon': selected_category.icon_class,  # Use the icon_class field from the ItemCategory model
                'category_title': f'{selected_category.name} Products',
                'category_description': selected_category.description,
            })
        except ItemCategory.DoesNotExist:
            pass  # If the category doesn't exist, keep the default hero data

    context = {
        'categories': categories,
        'items': items,
        'cart_count': cart_count,
        'search_query': search_query,
        **hero_data,
    }
    return render(request, 'home.html', context)

def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)

        cart_id = request.session.get('cart_id')
        if not cart_id:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.get(id=cart_id)

        item = get_object_or_404(Item, id=item_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            item=item,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        cart.update_total()

        return JsonResponse({
            'success': True,
            'cart_count': sum(item.quantity for item in cart.cartitem_set.all())
        })
    return JsonResponse({'success': False})

def cart(request):
    cart_id = request.session.get('cart_id')
    if cart_id:
        cart = Cart.objects.get(id=cart_id)
        cart_items = cart.cartitem_set.all()
    else:
        cart = None
        cart_items = []

    if request.method == "POST":
        referred_by = request.POST.get("referred_by", "").strip()
        billing_address = request.POST.get("billing_address", "").strip()

        if cart:
            if referred_by:
                cart.referred_by = referred_by
            if billing_address:
                cart.billing_address = billing_address
            cart.save()

    context = {
        'cart': cart,
        'cart_items': cart_items
    }
    return render(request, 'cart.html', context)


def update_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 0))

        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart_item = get_object_or_404(CartItem, cart=cart, item_id=item_id)

            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

            cart.update_total()

            return JsonResponse({
                'success': True,
                'total': str(cart.total_amount),
                'cart_count': sum(item.quantity for item in cart.cartitem_set.all())
            })
    return JsonResponse({'success': False})

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from datetime import datetime
from weasyprint import HTML

def generate_quotation(request):
    cart_id = request.session.get('cart_id')
    if cart_id:
        cart = Cart.objects.get(id=cart_id)
        referrer_phone = request.POST.get('referrer', '')
        billing_address = request.POST.get('billing_address', '')

        # Save the referrer phone number and billing address to the cart
        if referrer_phone:
            cart.referred_by = referrer_phone
        if billing_address:
            cart.billing_address = billing_address
        cart.save()

        cart_items = cart.cartitem_set.all()

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'whatsapp_number': '+260772447190',
            'referrer_phone': referrer_phone,
            'billing_address': billing_address
        }

        # Generate quotation HTML
        html_content = render_to_string('quotation_template.html', context)

        # Generate PDF using WeasyPrint
        pdf_file = HTML(string=html_content).write_pdf()

        # Save the PDF temporarily
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        pdf_filename = f"quotation_{timestamp}.pdf"
        pdf_path = default_storage.save(pdf_filename, ContentFile(pdf_file))

        # Generate downloadable link
        pdf_url = request.build_absolute_uri(default_storage.url(pdf_path))

        # Create WhatsApp message
        items_list = "\n".join([f"{item.quantity}x {item.item.name}" for item in cart_items])
        whatsapp_message = (
            f"New Order:\n{items_list}\nTotal: K{cart.total_amount}\n"
            f"Billing Address: {billing_address}\n"
            f"Download PDF: {pdf_url}"
        )

        if referrer_phone:
            whatsapp_message += f"\nReferred by: {referrer_phone}"

        whatsapp_url = f"https://wa.me/260772447190?text={whatsapp_message}"

        return JsonResponse({
            'success': True,
            'whatsapp_url': whatsapp_url,
            'pdf_url': pdf_url,
            'html_content': html_content
        })
    return JsonResponse({'success': False})
