from directory.models import Business, Category, BusinessPost
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

def format_business_result(biz, query=None):
    result = f"<div class='business-result'>"
    result += f"<strong>{biz.name}</strong>"
    
    # Highlight city if available
    if biz.city:
        city_display = biz.city
        if query and query.lower() in biz.city.lower():
            city_display = f"<span class='highlight'>{biz.city}</span>"
        result += f" in {city_display}"
    
    if biz.category:
        result += f" ({biz.category.name})"
    
    # Include matching posts if we have a query
    if query:
        matching_posts = get_matching_posts(biz, query)
        if matching_posts:
            result += "<div class='matching-posts'>"
            result += "<br><em>Matching posts:</em>"
            for post in matching_posts:
                result += f"<div class='post'>- {post.title}"
                if post.post_type:
                    result += f" ({post.post_type})"
                result += "</div>"
            result += "</div>"
    
    if biz.phone_number:
        result += f"<div class='business-info'>📞 {biz.phone_number}</div>"
    if biz.address:
        # Highlight address if it contains the query
        address_display = biz.address
        if query and query.lower() in biz.address.lower():
            address_display = f"<span class='highlight'>{biz.address}</span>"
        result += f"<div class='business-info'>📍 {address_display}</div>"
    result += "</div><br>"
    return result

def get_businesses_by_criteria(query=None, city=None, category_name=None, limit=10):
    queryset = Business.objects.filter(status='active')
    
    if city:
        # Handle city filtering more strictly
        queryset = queryset.filter(
            Q(city__iexact=city) | 
            Q(city__icontains=city) |
            Q(address__icontains=city)
        ).distinct()
    
    if query:
        query_words = query.split()
        q_objects = Q()
        
        # Exact match for business name should be highest priority
        q_objects |= Q(name__iexact=query)
        
        # Then partial matches in name
        for word in query_words:
            q_objects |= Q(name__icontains=word)
            
        # Then matches in description and posts
        for word in query_words:
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
    
    # Remove duplicates by business name
    seen_names = set()
    unique_businesses = []
    for biz in queryset.order_by('name'):
        if biz.name.lower() not in seen_names:
            seen_names.add(biz.name.lower())
            unique_businesses.append(biz)
        if len(unique_businesses) >= limit:
            break
    
    return unique_businesses

def get_all_businesses(limit=20):
    # Also apply duplicate removal for list_all
    queryset = Business.objects.filter(status='active')
    seen_names = set()
    unique_businesses = []
    for biz in queryset.order_by('name'):
        if biz.name.lower() not in seen_names:
            seen_names.add(biz.name.lower())
            unique_businesses.append(biz)
        if len(unique_businesses) >= limit:
            break
    return unique_businesses

def get_business_contact(business_name):
    try:
        business = Business.objects.filter(
            Q(name__iexact=business_name) |
            Q(name__icontains=business_name)
        ).first()
        if business:
            return {
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
    return Category.objects.all().values_list('name', flat=True)

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
    if not query:
        return business.posts.none()
    
    query_words = query.split()
    q_objects = Q()
    
    for word in query_words:
        q_objects |= Q(title__icontains=word) | Q(content__icontains=word)
    
    return business.posts.filter(q_objects)[:3]  # Limit to 3 matching posts