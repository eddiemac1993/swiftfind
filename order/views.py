from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Item, Cart, CartItem, Category
import json
from django.http import JsonResponse
from django.db.models import Exists, OuterRef

def get_cart(request):
    cart, created = Cart.objects.get_or_create(id=request.session.get('cart_id'))
    if created:
        request.session['cart_id'] = cart.id
    return cart


from django.db.models import Exists, OuterRef
from django.shortcuts import render
from .models import Category, Item, Cart

def home(request):
    # Annotate each category with a boolean field 'has_items' indicating if it has any associated items
    categories = Category.objects.annotate(
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
            selected_category = Category.objects.get(id=category_id)
            hero_data.update({
                'category_icon': selected_category.icon_class,  # Use the icon_class field from the Category model
                'category_title': f'{selected_category.name} Products',  # Dynamic title based on category
                'category_description': selected_category.description,  # Use the description field from the Category model
            })
        except Category.DoesNotExist:
            pass  # If the category doesn't exist, keep the default hero data

    context = {
        'categories': categories,
        'items': items,
        'cart_count': cart_count,
        'search_query': search_query,
        **hero_data,  # Include hero section data in the context
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
