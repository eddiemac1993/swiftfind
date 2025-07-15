from directory.models import Business, Category, BusinessPost
from django.db.models import Q
import logging
from django.utils.html import escape
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def format_website_url(url):
    if not url:
        return ""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"http://{url}"
    return url

def format_business_result(biz, query=None):
    result = f"<div class='business-result' data-id='{biz.id}'>"
    result += f"<strong><a href='/directory/{biz.id}/' class='business-link'>{escape(biz.name)}</a></strong>"

    # Location info
    if biz.city:
        city_display = escape(biz.city)
        if query and query.lower() in biz.city.lower():
            city_display = f"<span class='highlight'>{city_display}</span>"
        result += f" in {city_display}"

    if biz.category:
        result += f" ({escape(biz.category.name)})"

    # Matching posts
    if query:
        matching_posts = get_matching_posts(biz, query)
        if matching_posts:
            result += "<div class='matching-posts'>"
            result += "<br><em>Matching posts:</em>"
            for post in matching_posts:
                result += f"<div class='post'>- {escape(post.title)}"
                if post.post_type:
                    result += f" ({escape(post.post_type)})"
                result += "</div>"
            result += "</div>"

    # Contact info
    if biz.phone_number:
        result += f"<div class='business-info'>📞 <a href='tel:{biz.phone_number}'>{escape(biz.phone_number)}</a></div>"
    if biz.address:
        address_display = escape(biz.address)
        if query and query.lower() in biz.address.lower():
            address_display = f"<span class='highlight'>{address_display}</span>"
        result += f"<div class='business-info'>📍 {address_display}</div>"

    # Website and email
    if biz.website:
        website_url = format_website_url(biz.website)
        website_display = escape(website_url.replace('http://', '').replace('https://', ''))
        result += f"<div class='business-info'>🌐 <a href='{website_url}' target='_blank'>{website_display}</a></div>"
    if biz.email:
        result += f"<div class='business-info'>✉️ <a href='mailto:{biz.email}'>{escape(biz.email)}</a></div>"

    result += "</div><br>"
    return result

def get_businesses_by_criteria(query=None, city=None, category_name=None, limit=10):
    queryset = Business.objects.filter(status='active').prefetch_related('posts', 'tags')

    if city:
        queryset = queryset.filter(
            Q(city__iexact=city) |
            Q(city__icontains=city) |
            Q(address__icontains=city)
        ).distinct()

    if query:
        query_words = query.split()
        q_objects = Q()

        # Exact match has highest priority
        q_objects |= Q(name__iexact=query)

        # Then partial matches
        for word in query_words:
            q_objects |= Q(name__icontains=word)
            q_objects |= Q(description__icontains=word)
            q_objects |= Q(posts__title__icontains=word)
            q_objects |= Q(posts__content__icontains=word)
            q_objects |= Q(tags__name__iexact=word)

        queryset = queryset.filter(q_objects).distinct()

    if category_name:
        queryset = queryset.filter(
            Q(category__name__iexact=category_name) |
            Q(tags__name__iexact=category_name) |
            Q(name__icontains=category_name) |
            Q(description__icontains=category_name) |
            Q(posts__title__icontains=category_name) |
            Q(posts__content__icontains=category_name)
        ).distinct()

    # Remove duplicates while preserving order
    seen_names = set()
    unique_businesses = []
    for biz in queryset.order_by('name'):
        if biz.name.lower() not in seen_names:
            seen_names.add(biz.name.lower())
            unique_businesses.append(biz)
        if len(unique_businesses) >= limit:
            break

    return unique_businesses

def get_all_businesses(limit=50):
    """
    Get all active businesses with a limit to prevent performance issues
    """
    try:
        queryset = Business.objects.filter(status='active').order_by('name')

        # Remove duplicates while preserving order
        seen_names = set()
        unique_businesses = []
        for biz in queryset:
            if biz.name.lower() not in seen_names:
                seen_names.add(biz.name.lower())
                unique_businesses.append(biz)
            if len(unique_businesses) >= limit:
                break

        return unique_businesses
    except Exception as e:
        logger.error(f"Error getting all businesses: {e}")
        return []

def get_business_contact(business_name):
    try:
        business = Business.objects.filter(
            Q(name__iexact=business_name) |
            Q(name__icontains=business_name)
        ).first()

        if business:
            return {
                'name': business.name,
                'phone': business.phone_number,
                'email': business.email,
                'website': business.website,
                'address': business.address,
                'city': business.city
            }
        return None
    except Exception as e:
        logger.error(f"Error getting business contact: {e}")
        return None

def get_all_categories():
    return Category.objects.all().values_list('name', flat=True).order_by('name')

def get_business_details(business_name):
    try:
        return Business.objects.filter(
            Q(name__iexact=business_name) |
            Q(name__icontains=business_name)
        ).first()
    except Exception as e:
        logger.error(f"Error getting business details: {e}")
        return None

def get_matching_posts(business, query):
    if not query or not hasattr(business, 'posts'):
        return []

    query_words = query.split()
    q_objects = Q()

    for word in query_words:
        q_objects |= Q(title__icontains=word) | Q(content__icontains=word)

    return list(business.posts.filter(q_objects).order_by('-created_at')[:3])

# Add to your existing utils.py

def get_business_products(business_name, product_query=None):
    """
    Get products for a business, optionally filtered by query
    """
    try:
        from pos_system.models import Product, ProductCategory

        business = Business.objects.filter(
            Q(name__iexact=business_name) |
            Q(name__icontains=business_name)
        ).first()

        if not business:
            return None

        products = Product.objects.filter(business=business, is_active=True)

        if product_query:
            query_words = product_query.split()
            q_objects = Q()

            for word in query_words:
                q_objects |= Q(name__icontains=word)
                q_objects |= Q(description__icontains=word)
                q_objects |= Q(category__name__icontains=word)

            products = products.filter(q_objects)

        return {
            'business': business,
            'products': products.order_by('name')[:20]  # Limit to 20 products
        }
    except Exception as e:
        logger.error(f"Error getting business products: {e}")
        return None

def format_product_response(product):
    """
    Format a product for display in chat
    """
    response = f"<div class='product-result'>"
    response += f"<strong>{escape(product.name)}</strong>"

    if product.category:
        response += f" ({escape(product.category.name)})"

    response += f"<div class='product-info'>"
    response += f"💵 Price: {escape(str(product.price))}"

    if product.cost_price:
        response += f" | Cost: {escape(str(product.cost_price))}"

    if product.stock_quantity is not None:
        stock_status = ""
        if product.stock_quantity > 10:
            stock_status = "✅ In stock"
        elif product.stock_quantity > 0:
            stock_status = "⚠️ Low stock"
        else:
            stock_status = "❌ Out of stock"
        response += f" | Stock: {stock_status} ({product.stock_quantity})"

    response += "</div>"

    if product.description:
        response += f"<div class='product-desc'>{escape(product.description)}</div>"

    if product.location:
        response += f"<div class='product-location'>📍 {escape(product.location)}</div>"

    response += "</div>"
    return response

def get_business_full_details(business_name):
    """
    Get comprehensive details about a business
    """
    try:
        business = Business.objects.filter(
            Q(name__iexact=business_name) |
            Q(name__icontains=business_name)
        ).select_related('category').prefetch_related('posts', 'images').first()

        if not business:
            return None

        # Get 3 most recent posts
        recent_posts = business.posts.order_by('-created_at')[:3]

        # Get primary image if available
        primary_image = business.images.first()

        return {
            'business': business,
            'recent_posts': recent_posts,
            'primary_image': primary_image
        }
    except Exception as e:
        logger.error(f"Error getting business full details: {e}")
        return None