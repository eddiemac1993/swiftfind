from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from datetime import datetime, timedelta
import json
from decimal import Decimal, InvalidOperation
from django.db.models import Avg
from .models import Product, ProductCategory, OrderStatusUpdate, Sale, SaleItem, ProductView, RewardClaim
from directory.models import Business, Advertisement
from django.db.models.functions import Random
from django.shortcuts import render
from django.http import JsonResponse
from pos_system.models import Product
from directory.models import Business
from pos_system.services.ai_assistant import ask_chatgpt


from django.shortcuts import render
from pos_system.models import Product
from pos_system.services.ai_assistant import ask_chatgpt


def build_marketplace_context():
    """Build fresh marketplace context with structured data"""
    products = Product.objects.select_related("business", "business__category").filter(
        is_active=True, stock_quantity__gt=0
    )[:100]  # Limit for performance

    context = "Available Products and Businesses:\n\n"

    for product in products:
        business = product.business
        context += f"""
Product ID: {product.id}
Product: {product.name}
Description: {product.description or 'No description'}
Price: ZMW {product.price}
Stock: {product.stock_quantity}
Business ID: {business.id}
Business: {business.name}
Verified: {'Yes' if business.is_verified else 'No'}
Category: {business.category.name if business.category else 'Uncategorized'}
City: {business.city or 'Not specified'}
---
"""
    return context
import json
from decimal import Decimal
from django.http import JsonResponse

def serialize_businesses(businesses):
    serialized = []
    for biz in businesses:
        serialized.append({
            "business_id": biz["business_id"],
            "business_name": biz["business_name"],
            "verified": biz["verified"],
            "category": biz["category"],
            # convert logo to URL if exists
            "logo": biz["logo"].url if biz.get("logo") else None,
            "products": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "price": float(p["price"]) if isinstance(p["price"], Decimal) else p["price"],
                    "stock": p["stock"],
                    "description": p["description"],
                    # convert image to URL if exists
                    "image": p["image"].url if p.get("image") else None,
                    "url": p["url"],
                }
                for p in biz.get("products", [])
            ]
        })
    return serialized

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
import json
import markdown2
from django.urls import reverse

def ai_assistant_view(request):
    businesses = None
    answer = None
    summary = None

    if request.method == "POST":
        question = request.POST.get("question")
        if question:
            context = build_marketplace_context()

            system_prompt = {
                "role": "system",
                "content": (
                    "You are a smart AI marketplace and travel assistant. "
                    "RULES: "
                    "1. If the user asks about businesses or products, you MUST reply with ONLY valid JSON. "
                    "   JSON schema: "
                    "[{business_id: integer, business_name: string, verified: boolean, category: string, logo: string|null, "
                    "products: [{id: integer, name: string, price: number, stock: integer, description: string, image: string|null}]}]. "
                    "   - Only include products and businesses that actually exist in the database. "
                    "2. If no matching products exist, reply with plain text: 'No matching products found.' "
                    "3. If the user asks about tourism, travel, safaris, family trips, cultural visits, experiences, or activities "
                    "(including budget-related travel queries), reply in plain text with friendly suggestions. "
                    "4. If the user asks about how to use the platform (e.g., selling, registering, or how it works), reply in plain text. "
                    "5. Never mix JSON with plain text in the same response. "
                    "6. Always ensure the JSON strictly follows the schema and is valid."
                ),
            }


            chat_input = [
                system_prompt,
                {"role": "system", "content": context},
                {"role": "user", "content": question},
            ]

            raw_answer = ask_chatgpt(chat_input)

            try:
                # Try to parse as JSON first
                ai_businesses = json.loads(raw_answer.strip().strip("`").replace("json\n", ""))

                validated_businesses = []

                for ai_biz in ai_businesses:
                    try:
                        # Find actual business
                        if "business_id" in ai_biz:
                            business = Business.objects.get(id=ai_biz["business_id"], status="active")
                        else:
                            business = Business.objects.get(
                                name__iexact=ai_biz["business_name"],
                                status="active"
                            )

                        validated_products = []
                        for ai_product in ai_biz.get("products", []):
                            try:
                                if "id" in ai_product:
                                    product = Product.objects.get(
                                        id=ai_product["id"],
                                        business=business,
                                        is_active=True,
                                        stock_quantity__gt=0
                                    )
                                else:
                                    product = Product.objects.get(
                                        name__iexact=ai_product["name"],
                                        business=business,
                                        is_active=True,
                                        stock_quantity__gt=0
                                    )

                                validated_products.append({
                                    "id": product.id,
                                    "name": product.name,
                                    "price": float(product.price),  # ✅ Decimal → float
                                    "stock": product.stock_quantity,
                                    "description": product.description or "",
                                    "image": product.image.url if product.image else None,  # ✅ URL string
                                    "url": reverse("pos_system:product_detail", args=[product.id]),
                                })
                            except Product.DoesNotExist:
                                continue

                        if validated_products:
                            validated_businesses.append({
                                "business_id": business.id,
                                "business_name": business.name,
                                "verified": business.is_verified,
                                "category": business.category.name if business.category else "Uncategorized",
                                "logo": business.logo.url if business.logo else None,  # ✅ URL string
                                "products": validated_products,
                            })

                    except (Business.DoesNotExist, Business.MultipleObjectsReturned):
                        continue

                businesses = validated_businesses

                # Build summary
                if businesses:
                    product_summaries = []
                    for biz in businesses[:3]:
                        for product in biz["products"][:1]:
                            stock_status = (
                                "Hurry, only a few left!" if product["stock"] <= 5 else f"In stock: {product['stock']}"
                            )
                            product_summaries.append(
                                f"{product['name']} from {biz['business_name']} at ZMW {product['price']} ({stock_status})"
                            )

                    if product_summaries:
                        if len(product_summaries) == 1:
                            summary = f"I found {product_summaries[0]}. Would you like to view it?"
                        else:
                            summary = "Here are some options I found: " + "; ".join(product_summaries) + ". Which one do you prefer?"

            except json.JSONDecodeError:
                answer = markdown2.markdown(raw_answer)
            except Exception as e:
                answer = f"Error processing response: {str(e)}"

            from pos_system.models import ChatLog
            ChatLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                question=question,
                answer=answer if answer else json.dumps(businesses),
            )

    return render(
        request,
        "ai_assistant.html",
        {
            "answer": answer,
            "businesses": businesses,
            "summary": summary,
        },
    )


def product_fallback_view(request, product_name):
    """Fallback view when AI suggests products that might not exist"""
    products = Product.objects.filter(
        name__icontains=product_name,
        is_active=True,
        stock_quantity__gt=0
    ).select_related('business')[:10]

    return render(request, 'pos_system/product_fallback.html', {
        'products': products,
        'search_term': product_name
    })
import random

def marketplace_view(request):
    """Display marketplace with products in random order"""
    # Get active products from verified businesses with store link enabled
    products = Product.objects.filter(
        business__is_admin_added=True,
        business__show_store_link=True,
        is_active=True,
        stock_quantity__gt=0
    ).select_related('business', 'category').annotate(
        view_count=Count('views')
    )

    # Convert to list and shuffle for random ordering (more efficient than Random() for large datasets)
    products_list = list(products)
    random.shuffle(products_list)

    # Get all distinct categories that have products matching our filters
    categories = ProductCategory.objects.filter(
        product__in=products
    ).distinct()

    # Get unique businesses for the business filter
    unique_businesses = Business.objects.filter(
        id__in=products.values_list('business', flat=True).distinct(),
        status='active'
    )

    context = {
        'products': products_list,
        'categories': categories,
        'unique_businesses': unique_businesses,
        'all_businesses': True  # Flag to show business filter
    }
    return render(request, 'pos_system/marketplace.html', context)

# In your pos_system/views.py

from django.views.decorators.http import require_GET
from django.contrib.sessions.backends.db import SessionStore
from django.db.models import Count, Sum
from decimal import Decimal
@require_GET
def product_detail(request, product_id):
    """Product detail page with view tracking"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)

        # Track the view
        track_product_view(request, product_id)

        # Get related products
        related_products = Product.objects.filter(
            business=product.business,
            is_active=True,
            stock_quantity__gt=0
        ).exclude(id=product.id).order_by('?')[:4]  # Random 4 related products

        # Get active advertisements
        now = timezone.now()
        advertisements = Advertisement.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        ).order_by('slot')

        context = {
            'product': product,
            'related_products': related_products,
            'business': product.business,
            'advertisements': advertisements
        }

        return render(request, 'pos_system/product_detail.html', context)

    except Exception as e:
        messages.error(request, f"Error loading product: {str(e)}")
        return redirect('pos_system:public_store_all')

from django.views.decorators.http import require_GET
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
# pos_system/views.py (updated)
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q

@csrf_exempt
@csrf_exempt
def track_product_view(request, product_id):
    """
    Tracks product views with the following behavior:
    - Only counts views from logged-in users
    - Counts only once per user per product (unique count)
    - Still tracks anonymous views but doesn't count them
    """
    try:
        product = Product.objects.get(id=product_id)

        # Initialize response data
        response_data = {
            'success': True,
            'views_count': product.views.count(),
            'new_view': False,
            'user_authenticated': request.user.is_authenticated
        }

        # Only process counting for authenticated users
        if request.user.is_authenticated:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

            # Determine if traffic is organic
            referrer = request.META.get('HTTP_REFERER', '')
            is_organic = bool(referrer) and request.get_host() not in referrer

            # Try to create new view record for authenticated user
            view, created = ProductView.objects.get_or_create(
                product=product,
                viewer=request.user,
                defaults={
                    'ip_address': ip,
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                    'referrer': referrer[:500],
                    'is_organic': is_organic,
                    'source': request.GET.get('source', 'direct'),
                    'viewed_at': timezone.now()
                }
            )

            # Update response data if this was a new view
            if created:
                response_data.update({
                    'views_count': product.views.count(),
                    'new_view': True
                })

        return JsonResponse(response_data)

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


from django.conf import settings
reward_per_view = settings.REWARD_PER_VIEW

from django.conf import settings
from decimal import Decimal
# ... other imports ...

@login_required
def product_analytics(request):
    """Business owner's product analytics dashboard"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    try:
        # Get view statistics for the business's products
        view_stats = Product.objects.filter(business=business).annotate(
            total_views=Count('views'),
            unclaimed_views=Count('views', filter=Q(views__claimed=False)),
            last_7_days_views=Count('views', filter=Q(
                views__viewed_at__gte=timezone.now() - timedelta(days=7),
                views__claimed=False
            )),
            last_30_days_views=Count('views', filter=Q(
                views__viewed_at__gte=timezone.now() - timedelta(days=30),
                views__claimed=False
            ))
        ).order_by('-total_views')

        # Calculate estimated rewards using the setting
        total_unclaimed_views = sum(p.unclaimed_views for p in view_stats)
        estimated_revenue = total_unclaimed_views * settings.REWARD_PER_VIEW

        # Get pending and approved claims
        claims = RewardClaim.objects.filter(business=business).order_by('-requested_at')

        context = {
            'business': business,
            'view_stats': view_stats,
            'total_views': total_unclaimed_views,
            'estimated_revenue': estimated_revenue,
            'reward_per_view': settings.REWARD_PER_VIEW,  # Pass the setting to template
            'claims': claims,
        }

        return render(request, 'pos_system/product_analytics.html', context)

    except Exception as e:
        messages.error(request, f"Error loading analytics: {str(e)}")
        return redirect('pos_system:dashboard')

@login_required
def claim_rewards(request):
    """Handle reward claims from business owners"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    if request.method == 'POST':
        try:
            # Get last 30 days unclaimed views
            last_30_days = timezone.now() - timedelta(days=30)
            unclaimed_views = ProductView.objects.filter(
                product__business=business,
                viewed_at__gte=last_30_days,
                claimed=False
            )

            views_count = unclaimed_views.count()

            if views_count == 0:
                messages.error(request, "No unclaimed views available to claim rewards for")
                return redirect('pos_system:product_analytics')

            # Calculate reward amount using the setting
            amount = Decimal(views_count) * settings.REWARD_PER_VIEW

            # Create claim
            claim = RewardClaim.objects.create(
                business=business,
                amount=amount,
                views_count=views_count
            )

            # Mark views as claimed
            unclaimed_views.update(claimed=True, claimed_at=timezone.now(), claim=claim)

            messages.success(request, f"Reward claim for ZMW {amount:.2f} submitted for review")
            return redirect('pos_system:product_analytics')

        except Exception as e:
            messages.error(request, f"Error submitting claim: {str(e)}")
            return redirect('pos_system:product_analytics')

    return redirect('pos_system:product_analytics')

def get_user_business(request):
    """Helper function to get user's business with proper error handling"""
    if not request.user.is_authenticated:
        return None, "Please log in to access this page."

    # Changed from business_set to owned_businesses to match your model
    business = request.user.owned_businesses.first()
    if not business:
        return None, "No business associated with your account."
    return business, None

from django.views.decorators.cache import cache_page

def public_store_all(request):
    """Show all products from all active businesses"""
    products = Product.objects.filter(
        business__status='active',
        is_active=True,
        stock_quantity__gt=0
    ).select_related('business', 'category').order_by(Random())

    # Get all distinct categories that have products matching our filters
    categories = ProductCategory.objects.filter(
        product__in=products
    ).distinct()

    # Alternative approach that might work better:
    # categories = ProductCategory.objects.filter(
    #     product__business__status='active',
    #     product__is_active=True,
    #     product__stock_quantity__gt=0
    # ).distinct()

    # Get unique businesses for the business filter
    unique_businesses = Business.objects.filter(
        id__in=products.values_list('business', flat=True).distinct(),
        status='active'
    )

    context = {
        'products': products,
        'categories': categories,
        'unique_businesses': unique_businesses,
        'all_businesses': True
    }
    return render(request, 'pos_system/public_store.html', context)

@cache_page(60 * 15)  # Cache for 15 minutes
def public_store(request, business_slug):
    """Public e-commerce page for a business"""
    business = get_object_or_404(Business, slug=business_slug, status='active')

    try:
        # Get active products with stock > 0
        products = Product.objects.filter(
            business=business,
            is_active=True,
            stock_quantity__gt=0
        ).select_related('category').order_by(Random())

        categories = ProductCategory.objects.filter(business=business)

        context = {
            'business': business,
            'products': products,
            'categories': categories,
        }

        return render(request, 'pos_system/public_store.html', context)

    except Exception as e:
        return render(request, 'pos_system/public_store.html', {
            'business': business,
            'error': str(e)
        })

@login_required
def dashboard(request):
    """Main dashboard view"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('directory:business_list')

    today = timezone.now().date()

    try:
        today_sales = Sale.objects.filter(
            business=business,
            created_at__date=today
        ).aggregate(
            total_sales=Sum('total'),
            total_transactions=Count('id')
        )

        product_stats = Product.objects.filter(
            business=business,
            is_active=True
        ).aggregate(
            total_products=Count('id'),
            low_stock=Count('id', filter=Q(stock_quantity__lte=5))
        )

        recent_sales = Sale.objects.filter(business=business).select_related('customer').order_by('-created_at')[:5]

        context = {
            'business': business,
            'today_sales': today_sales['total_sales'] or 0,
            'today_transactions': today_sales['total_transactions'] or 0,
            'total_products': product_stats['total_products'] or 0,
            'low_stock_products': product_stats['low_stock'] or 0,
            'recent_sales': recent_sales,
        }

        return render(request, 'pos_system/dashboard.html', context)

    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('pos_system:dashboard')


@login_required
def pos_view(request):
    """POS interface view"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    try:
        # Get active products with stock > 0
        products = Product.objects.filter(
            business=business,
            is_active=True,
            stock_quantity__gt=0
        ).select_related('category').order_by('name')

        categories = ProductCategory.objects.filter(business=business)

        context = {
            'business': business,
            'initial_products': products,  # This is what your template expects
            'categories': categories,
        }

        return render(request, 'pos_system/pos.html', context)

    except Exception as e:
        messages.error(request, f"Error loading POS: {str(e)}")
        return redirect('pos_system:dashboard')

    except Exception as e:
        messages.error(request, f"Error loading POS: {str(e)}")
        return redirect('pos_system:dashboard')


@login_required
def search_products(request):
    """AJAX view for product search"""
    business, error = get_user_business(request)
    if error:
        return JsonResponse({'success': False, 'message': error})

    search_query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', 'all')

    products = Product.objects.filter(
        business=business,
        is_active=True,
        stock_quantity__gt=0
    ).select_related('category')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )

    if category_id != 'all':
        try:
            products = products.filter(category_id=int(category_id))
        except ValueError:
            pass

    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'image_url': product.image.url if product.image else '/static/images/default-product.png',
            'category': product.category.name if product.category else 'Uncategorized',
            'stock_quantity': product.stock_quantity,
            'stock_class': product.get_stock_status_class()
        })

    return JsonResponse({
        'success': True,
        'products': products_data
    })

@login_required
def add_to_cart(request):
    """AJAX view to add product to cart"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    try:
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)

        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        if not product_id:
            return JsonResponse({'success': False, 'message': 'Product ID is required'}, status=400)

        if quantity <= 0:
            return JsonResponse({'success': False, 'message': 'Quantity must be positive'}, status=400)

        business, error = get_user_business(request)
        if error:
            return JsonResponse({'success': False, 'message': error}, status=403)

        try:
            product = Product.objects.get(id=product_id, business=business)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)

        if product.stock_quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {product.stock_quantity} available in stock'
            }, status=400)

        # Get or initialize cart
        cart = request.session.get('cart', {})
        product_key = str(product_id)

        # Update cart
        if product_key in cart:
            cart[product_key]['quantity'] += quantity
        else:
            cart[product_key] = {
                'name': product.name,
                'price': str(product.price),
                'quantity': quantity
            }

        # Save to session
        request.session['cart'] = cart
        request.session.modified = True

        # Return updated cart info
        cart_item_count = sum(item['quantity'] for item in cart.values())
        cart_total = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())

        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_item_count': cart_item_count,
            'cart_total': str(cart_total),
            'cart': cart
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@login_required
def sale_detail(request, sale_id):
    """View sale details with improved error handling"""
    business, error = get_user_business(request)
    if error:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': error,
                'error_type': 'business_error'
            }, status=403)
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    try:
        sale = get_object_or_404(Sale, id=sale_id, business=business)
        items = sale.pos_system_items.select_related('product')

        items_data = [{
            'product': {
                'name': item.product.name,
                'id': item.product.id,
            },
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'total_price': str(item.total_price)
        } for item in items]

        response_data = {
            'success': True,
            'sale': {
                'id': sale.id,
                'transaction_id': sale.transaction_id,
                'subtotal': str(sale.subtotal),
                'tax': str(sale.tax),
                'discount': str(sale.discount),
                'total': str(sale.total),
                'created_at': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            },
            'items': items_data
        }

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(response_data)

        # Regular HTML response
        context = {
            'business': business,
            'sale': sale,
            'items': items,
        }
        return render(request, 'pos_system/sale_detail.html', context)

    except Exception as e:
        error_message = f"Error loading sale details: {str(e)}"
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': error_message,
                'error_type': 'processing_error'
            }, status=500)

        messages.error(request, error_message)
        return redirect('pos_system:sales_report')

@login_required
def remove_from_cart(request):
    """AJAX view to remove product from cart"""
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")

    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))

        cart = request.session.get('cart', {})

        if product_id in cart:
            del cart[product_id]
            request.session['cart'] = cart
            request.session.modified = True

            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_item_count': sum(item['quantity'] for item in cart.values())
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def update_cart_item(request):
    """AJAX view to update cart item quantity"""
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")

    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity', 0))

        if quantity < 0:
            return JsonResponse({
                'success': False,
                'message': 'Quantity cannot be negative'
            })

        business, error = get_user_business(request)
        if error:
            return JsonResponse({
                'success': False,
                'message': error
            })

        cart = request.session.get('cart', {})

        if product_id not in cart:
            return JsonResponse({
                'success': False,
                'message': 'Product not in cart'
            })

        product = get_object_or_404(Product, id=product_id, business=business)

        if quantity == 0:
            del cart[product_id]
        else:
            if product.stock_quantity < quantity:
                return JsonResponse({
                    'success': False,
                    'message': 'Insufficient stock'
                })
            cart[product_id]['quantity'] = quantity

        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'cart_item_count': sum(item['quantity'] for item in cart.values())
        })

    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid quantity'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def get_cart(request):
    """AJAX view to get current cart"""
    try:
        cart = request.session.get('cart', {})
        total = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())

        return JsonResponse({
            'success': True,
            'cart': cart,
            'total': str(total),
            'item_count': sum(item['quantity'] for item in cart.values())
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def inventory_view(request):
    """Inventory management view"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    try:
        product_list = Product.objects.filter(business=business).order_by('name')

        paginator = Paginator(product_list, 20)
        page = request.GET.get('page')

        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

        context = {
            'business': business,
            'products': products,
        }

        return render(request, 'pos_system/inventory.html', context)

    except Exception as e:
        messages.error(request, f"Error loading inventory: {str(e)}")
        return redirect('pos_system:dashboard')

@login_required
def add_product(request):
    """Add new product"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    categories = ProductCategory.objects.filter(business=business)

    if request.method == 'POST':
        try:
            price = Decimal(request.POST.get('price', 0))
            cost_price = Decimal(request.POST.get('cost_price', 0))
            stock_quantity = int(request.POST.get('stock_quantity', 0))
            unit = request.POST.get('unit', 'piece')  # 👈 Get unit from form

            product = Product(
                business=business,
                name=request.POST.get('name').strip(),
                description=request.POST.get('description', '').strip(),
                price=price,
                cost_price=cost_price,
                stock_quantity=stock_quantity,
                unit=unit,  # 👈 Add unit here
                barcode=request.POST.get('barcode', '').strip(),
                sku=request.POST.get('sku', '').strip(),
                location=request.POST.get('location', '').strip(),
                is_active=True
            )

            category_id = request.POST.get('category')
            if category_id:
                product.category = ProductCategory.objects.get(id=category_id, business=business)

            if 'image' in request.FILES:
                product.image = request.FILES['image']

            product.save()

            messages.success(request, f"Product '{product.name}' added successfully!")
            return redirect('pos_system:inventory')

        except InvalidOperation:
            messages.error(request, "Invalid price or cost price value")
        except Exception as e:
            messages.error(request, f"Error adding product: {str(e)}")

    context = {
        'business': business,
        'categories': categories,
    }

    return render(request, 'pos_system/add_product.html', context)

@login_required
def edit_product(request, product_id):
    """Edit existing product"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    product = get_object_or_404(Product, id=product_id, business=business)
    categories = ProductCategory.objects.filter(business=business)

    if request.method == 'POST':
        try:
            product.name = request.POST.get('name').strip()
            product.description = request.POST.get('description', '').strip()
            product.price = Decimal(request.POST.get('price', 0))
            product.cost_price = Decimal(request.POST.get('cost_price', 0))
            product.stock_quantity = int(request.POST.get('stock_quantity', 0))
            product.unit = request.POST.get('unit', 'piece')  # 👈 Add unit update
            product.barcode = request.POST.get('barcode', '').strip()
            product.sku = request.POST.get('sku', '').strip()
            product.location = request.POST.get('location', '').strip()
            product.is_active = request.POST.get('is_active') == 'on'

            category_id = request.POST.get('category')
            if category_id:
                product.category = ProductCategory.objects.get(id=category_id, business=business)
            else:
                product.category = None

            if 'image' in request.FILES:
                product.image = request.FILES['image']

            product.save()

            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('pos_system:inventory')

        except InvalidOperation:
            messages.error(request, "Invalid price or cost price value")
        except Exception as e:
            messages.error(request, f"Error updating product: {str(e)}")

    context = {
        'business': business,
        'product': product,
        'categories': categories,
    }

    return render(request, 'pos_system/edit_product.html', context)

@login_required
def delete_product(request, product_id):
    """Delete a product"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    product = get_object_or_404(Product, id=product_id, business=business)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully')
        return redirect('pos_system:inventory')

    return render(request, 'pos_system/confirm_delete_product.html', {
        'product': product
    })

@login_required
def print_receipt(request, sale_id):
    """View for printing receipts"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    sale = get_object_or_404(Sale, id=sale_id, business=business)
    items = sale.pos_system_items.select_related('product')

    context = {
        'business': business,
        'sale': sale,
        'items': items,
    }

    return render(request, 'pos_system/receipt.html', context)

@login_required
def category_list(request):
    """List all categories"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    categories = ProductCategory.objects.filter(business=business).order_by('name')

    context = {
        'business': business,
        'categories': categories,
    }

    return render(request, 'pos_system/category_list.html', context)


@login_required
def add_category(request):
    """Add new category"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    if request.method == 'POST':
        try:
            name = request.POST.get('name').strip()
            if not name:
                raise ValueError("Category name cannot be empty")

            ProductCategory.objects.create(
                business=business,
                name=name
            )
            messages.success(request, "Category added successfully!")
            return redirect('pos_system:category_list')

        except Exception as e:
            messages.error(request, f"Error adding category: {str(e)}")

    context = {
        'business': business,
    }

    return render(request, 'pos_system/add_category.html', context)


@login_required
def edit_category(request, category_id):
    """Edit category"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    category = get_object_or_404(ProductCategory, id=category_id, business=business)

    if request.method == 'POST':
        try:
            name = request.POST.get('name').strip()
            if not name:
                raise ValueError("Category name cannot be empty")

            category.name = name
            category.save()
            messages.success(request, "Category updated successfully!")
            return redirect('pos_system:category_list')

        except Exception as e:
            messages.error(request, f"Error updating category: {str(e)}")

    context = {
        'business': business,
        'category': category,
    }

    return render(request, 'pos_system/edit_category.html', context)


@login_required
def confirm_delete_category(request, category_id):
    """View to confirm category deletion"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:category_list')

    category = get_object_or_404(ProductCategory, id=category_id, business=business)

    # Check if category is being used by any products
    products_using_category = Product.objects.filter(category=category).exists()

    if request.method == 'POST':
        try:
            category_name = category.name
            category.delete()
            messages.success(request, f"Category '{category_name}' deleted successfully!")
            return redirect('pos_system:category_list')
        except Exception as e:
            messages.error(request, f"Error deleting category: {str(e)}")
            return redirect('pos_system:category_list')

    context = {
        'business': business,
        'category': category,
        'products_using_category': products_using_category,
    }

    return render(request, 'pos_system/confirm_delete_category.html', context)


@login_required
def delete_category(request, category_id):
    """Actual category deletion view (handles POST only)"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:category_list')

    if request.method == 'POST':
        category = get_object_or_404(ProductCategory, id=category_id, business=business)
        try:
            category_name = category.name
            category.delete()
            messages.success(request, f"Category '{category_name}' deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting category: {str(e)}")

    return redirect('pos_system:category_list')

@login_required
def admin_dashboard(request):
    """Admin dashboard with comprehensive stats"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    try:
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Sales statistics
        sales_data = {
            'today': Sale.objects.filter(business=business, created_at__date=today),
            'week': Sale.objects.filter(business=business, created_at__date__gte=week_ago),
            'month': Sale.objects.filter(business=business, created_at__date__gte=month_ago),
        }

        stats = {}
        for period, queryset in sales_data.items():
            stats[f'{period}_total'] = queryset.aggregate(Sum('total'))['total__sum'] or 0
            stats[f'{period}_transactions'] = queryset.count()

        # Product statistics
        product_stats = Product.objects.filter(business=business, is_active=True).aggregate(
            total=Count('id'),
            low_stock=Count('id', filter=Q(stock_quantity__lte=5)),
            out_of_stock=Count('id', filter=Q(stock_quantity=0))
        )

        low_stock_products = Product.objects.filter(
            business=business,
            is_active=True,
            stock_quantity__lte=5
        )[:10]

        context = {
            'business': business,
            **stats,
            **product_stats,
            'low_stock_products': low_stock_products,
        }

        return render(request, 'pos_system/admin_dashboard.html', context)

    except Exception as e:
        messages.error(request, f"Error loading admin dashboard: {str(e)}")
        return redirect('pos_system:dashboard')

@login_required
def reports_view(request):
    """Reports main page with options for different report types"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    try:
        # Get basic stats for the reports page
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)

        sales_stats = Sale.objects.filter(
            business=business,
            created_at__date__gte=month_ago
        ).aggregate(
            total_sales=Sum('total'),
            avg_sale=Avg('total'),
            total_transactions=Count('id')
        )

        product_stats = Product.objects.filter(
            business=business
        ).aggregate(
            total_products=Count('id'),
            active_products=Count('id', filter=Q(is_active=True)),
            out_of_stock=Count('id', filter=Q(stock_quantity=0))
        )

        context = {
            'business': business,
            'sales_stats': sales_stats,
            'product_stats': product_stats,
            'report_types': [
                {'name': 'Sales Report', 'url': 'pos_system:sales_report'},
                {'name': 'Inventory Report', 'url': 'pos_system:inventory'},
                {'name': 'Product Performance', 'url': 'pos_system:product_performance_report'},
            ]
        }

        return render(request, 'pos_system/reports.html', context)

    except Exception as e:
        messages.error(request, f"Error loading reports: {str(e)}")
        return redirect('pos_system:dashboard')


@login_required
def product_performance_report(request):
    """Product performance report showing top/bottom selling products"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    try:
        # Date range filtering
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        sale_items = SaleItem.objects.filter(
            sale__business=business
        ).select_related('product', 'sale')

        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                sale_items = sale_items.filter(sale__created_at__date__gte=start_date)
            except ValueError:
                messages.error(request, "Invalid start date format.")

        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                sale_items = sale_items.filter(sale__created_at__date__lte=end_date)
            except ValueError:
                messages.error(request, "Invalid end date format.")

        # Get top and bottom performing products
        product_performance = sale_items.values(
            'product__name',
            'product__id'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('total_price'),
            sale_count=Count('sale', distinct=True)
        ).order_by('-total_revenue')

        top_products = product_performance[:10]
        bottom_products = product_performance.order_by('total_revenue')[:10]

        context = {
            'business': business,
            'top_products': top_products,
            'bottom_products': bottom_products,
            'start_date': start_date,
            'end_date': end_date,
        }

        return render(request, 'pos_system/product_performance_report.html', context)

    except Exception as e:
        messages.error(request, f"Error generating product performance report: {str(e)}")
        return redirect('pos_system:reports')

@login_required
def sales_report(request):
    """Sales report with filtering"""
    business, error = get_user_business(request)
    if error:
        messages.error(request, error)
        return redirect('pos_system:dashboard')

    try:
        sales = Sale.objects.filter(business=business).order_by('-created_at')

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                sales = sales.filter(created_at__date__gte=start_date)
            except ValueError:
                messages.error(request, "Invalid start date format.")

        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                sales = sales.filter(created_at__date__lte=end_date)
            except ValueError:
                messages.error(request, "Invalid end date format.")

        total_sales = sales.aggregate(Sum('total'))['total__sum'] or 0
        total_transactions = sales.count()

        paginator = Paginator(sales, 20)
        page = request.GET.get('page')

        try:
            sales_page = paginator.page(page)
        except PageNotAnInteger:
            sales_page = paginator.page(1)
        except EmptyPage:
            sales_page = paginator.page(paginator.num_pages)

        context = {
            'business': business,
            'sales': sales_page,
            'total_sales': total_sales,
            'total_transactions': total_transactions,
            'start_date': start_date,
            'end_date': end_date,
        }

        return render(request, 'pos_system/sales_report.html', context)

    except Exception as e:
        messages.error(request, f"Error loading sales report: {str(e)}")
        return redirect('pos_system:dashboard')



@login_required
def clear_cart(request):
    """AJAX view to clear the cart"""
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")

    try:
        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True

        return JsonResponse({
            'success': True,
            'message': 'Cart cleared'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def process_sale(request):
    """AJAX view to process sale"""
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")

    try:
        data = json.loads(request.body)
        cart = request.session.get('cart', {})

        if not cart:
            return JsonResponse({
                'success': False,
                'message': 'Cart is empty'
            })

        business, error = get_user_business(request)
        if error:
            return JsonResponse({
                'success': False,
                'message': error
            })

        # Validate all products in cart
        product_ids = [int(pid) for pid in cart.keys()]
        products = Product.objects.filter(id__in=product_ids, business=business)

        if len(products) != len(cart):
            return JsonResponse({
                'success': False,
                'message': 'Some products in cart are no longer available'
            })

        # Calculate totals
        subtotal = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())
        tax = Decimal(data.get('tax', 0))
        discount = Decimal(data.get('discount', 0))
        total = subtotal + tax - discount

        # Create sale
        sale = Sale.objects.create(
            business=business,
            transaction_id=f"TXN{timezone.now().strftime('%Y%m%d%H%M%S')}",
            subtotal=subtotal,
            tax=tax,
            discount=discount,
            total=total,
            payment_method=data.get('payment_method', 'cash'),
            notes=data.get('notes', '').strip(),
            created_by=request.user
        )

        # Create sale items and update stock
        for product_id, item in cart.items():
            product = next(p for p in products if p.id == int(product_id))

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=item['quantity'],
                unit_price=Decimal(item['price']),
                total_price=Decimal(item['price']) * item['quantity']
            )

            # Update stock
            product.stock_quantity -= item['quantity']
            product.save()

        # Clear cart
        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True

        return JsonResponse({
            'success': True,
            'message': 'Sale completed successfully',
            'transaction_id': sale.transaction_id,
            'sale_id': sale.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
import json
from .models import Order, OrderItem, Product
from .utils import send_order_notification

@require_POST
@csrf_exempt
def create_order(request):
    try:
        # Check content type
        if not request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'Invalid content type',
                'details': 'Expected application/json'
            }, status=400)

        # Parse JSON data from request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data',
                'details': str(e)
            }, status=400)

        # Validate required fields
        required_fields = ['business_id', 'customer_name', 'customer_phone', 'items']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required field',
                    'details': f'Field "{field}" is required'
                }, status=400)

        # Validate items
        if not isinstance(data['items'], list) or len(data['items']) == 0:
            return JsonResponse({
                'success': False,
                'error': 'Invalid items data',
                'details': 'Order must contain at least one item'
            }, status=400)

        with transaction.atomic():
            # Create the order
            order = Order.objects.create(
                business_id=data['business_id'],
                customer_name=data['customer_name'],
                customer_phone=data['customer_phone'],
                customer_notes=data.get('customer_notes', ''),
                subtotal=Decimal(str(data.get('subtotal', 0))),
                delivery_fee=Decimal(str(data.get('delivery_fee', 0))),
                total=Decimal(str(data.get('total', 0))),
                status='pending'
            )

            # Create order items with product validation
            order_items = []
            for item in data['items']:
                try:
                    product = Product.objects.get(pk=item['product_id'])
                except Product.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid product',
                        'details': f"Product with ID {item['product_id']} does not exist"
                    }, status=400)

                order_items.append(OrderItem(
                    order=order,
                    product=product,
                    product_name=item.get('name', product.name),
                    quantity=item['quantity'],
                    price=Decimal(str(item['price'])),
                    business_name=item.get('business', '')
                ))

            OrderItem.objects.bulk_create(order_items)

        # Send notifications
        try:
            send_order_notification(order, to_business=True)
            send_order_notification(order, to_customer=True)
        except Exception as e:
            # Don't fail the order if notification fails
            print(f"Failed to send notification: {str(e)}")

        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number,
            'message': 'Order received successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }, status=500)


def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
        'order_items': order.items.all()  # Changed from orderitem_set to items
    }
    return render(request, 'pos_system/order_details.html', context)

# views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone

@require_POST
@login_required
def submit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    if order.submitted:
        return JsonResponse({
            'success': False,
            'error': 'This order has already been submitted'
        })

    # Mark order as submitted
    order.submitted = True
    order.submitted_at = timezone.now()
    order.save()

    # Create message content
    message = f"New Order #{order.id}\n\n"
    message += f"Customer: {order.customer_name}\n"
    message += f"Phone: {order.customer_phone}\n\n"

    if request.POST.get('customer_message'):
        message += f"Customer Message: {request.POST['customer_message']}\n\n"

    message += "Order Items:\n"
    for item in order.items.all():
        message += f"- {item.product_name} ({item.quantity} × {item.price}) = {item.quantity * item.price}\n"

    message += f"\nSubtotal: {order.subtotal}\n"
    message += f"Delivery Fee: {order.delivery_fee}\n"
    message += f"Total: {order.total}\n\n"
    message += "Please confirm this order. Thank you!"

    # Start conversation with business owner
    try:
        conversation = Conversation.objects.create(
            sender=request.user,
            recipient=order.business.owner,
            subject=f"Order #{order.id}",
            initial_message=message
        )

        # You might also want to create a notification for the business owner

        return JsonResponse({
            'success': True,
            'message': 'Order submitted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def customer_orders(request):
    """View for customer to see their orders"""
    print(f"Current user: {request.user}")  # Debug
    print(f"User email: {request.user.email}")  # Debug
    print(f"User full name: {request.user.get_full_name()}")  # Debug

    orders = Order.objects.filter(
        Q(customer_name=request.user.get_full_name()) |
        Q(customer_email=request.user.email)
    ).order_by('-created_at')

    print(f"Found orders count: {orders.count()}")  # Debug

    # Mark orders as read when viewed by customer
    orders.filter(is_read=False).update(is_read=True)

    context = {
        'orders': orders
    }
    return render(request, 'pos_system/customer_orders.html', context)

@login_required
def business_orders(request):
    """View for business owner to see received orders"""
    business = get_object_or_404(Business, owner=request.user)
    orders = Order.objects.filter(business=business).order_by('-created_at')

    # Mark orders as read when viewed by business
    orders.filter(is_read_business=False).update(is_read_business=True)

    context = {
        'business': business,
        'orders': orders
    }
    return render(request, 'pos_system/business_orders.html', context)

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

@require_POST
@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Check if user has permission (business owner or staff)
    if not (request.user == order.business.owner or request.user in order.business.staff.all()):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')

    if new_status not in dict(Order.ORDER_STATUS).keys():
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

    # Create status update record
    OrderStatusUpdate.objects.create(
        order=order,
        status=new_status,
        notes=notes,
        updated_by=request.user
    )

    # Update order status
    previous_status = order.status
    order.status = new_status
    order.save()

    # Prepare response data
    response_data = {
        'success': True,
        'new_status': order.get_status_display(),
        'status_class': get_status_class(order.status),
        'status_icon': get_status_icon(order.status),
        'updated_at': order.updated_at.strftime("%b %d, %Y %H:%M"),
        'updated_by': request.user.get_full_name() or request.user.username
    }

    return JsonResponse(response_data)

@login_required
def direct_status_update(request, order_id, status):
    order = get_object_or_404(Order, id=order_id)

    # Check permissions
    if not (request.user == order.business.owner or request.user in order.business.staff.all()):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if status not in dict(Order.ORDER_STATUS).keys():
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

    # Create status update record
    OrderStatusUpdate.objects.create(
        order=order,
        status=status,
        updated_by=request.user
    )

    # Update order status
    order.status = status
    order.save()

    return JsonResponse({
        'success': True,
        'message': f'Order status updated to {status}'
    })

# Helper functions
def get_status_class(status):
    return {
        'pending': 'status-pending',
        'confirmed': 'status-confirmed',
        'processing': 'status-processing',
        'shipped': 'status-shipped',
        'delivered': 'status-delivered',
        'cancelled': 'status-cancelled'
    }.get(status, 'status-pending')

def get_status_icon(status):
    return {
        'pending': 'fa-clock',
        'confirmed': 'fa-check',
        'processing': 'fa-cog fa-spin',
        'shipped': 'fa-truck',
        'delivered': 'fa-box-open',
        'cancelled': 'fa-times-circle'
    }[status]
