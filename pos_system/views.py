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
from .models import Product, ProductCategory, Sale, SaleItem
from directory.models import Business

def marketplace_view(request):
    # Get active products from verified businesses with store link enabled
    products = Product.objects.filter(
        business__is_admin_added=True,
        business__show_store_link=True,
        is_active=True,
        stock_quantity__gt=0
    ).select_related('business', 'category').order_by('name')

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
        'products': products,
        'categories': categories,
        'unique_businesses': unique_businesses,
        'all_businesses': True  # Flag to show business filter
    }
    return render(request, 'pos_system/marketplace.html', context)

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
    ).select_related('business', 'category').order_by('name')

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
        ).select_related('category').order_by('name')

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

            product = Product(
                business=business,
                name=request.POST.get('name').strip(),
                description=request.POST.get('description', '').strip(),
                price=price,
                cost_price=cost_price,
                stock_quantity=stock_quantity,
                barcode=request.POST.get('barcode', '').strip(),
                sku=request.POST.get('sku', '').strip(),
                location=request.POST.get('location', '').strip(),  # Add this line
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
            product.barcode = request.POST.get('barcode', '').strip()
            product.sku = request.POST.get('sku', '').strip()
            product.location = request.POST.get('location', '').strip()  # Add this line
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
