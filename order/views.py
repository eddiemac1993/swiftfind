from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Item, Cart, CartItem, Category
import json
from django.http import JsonResponse

def get_cart(request):
    cart, created = Cart.objects.get_or_create(id=request.session.get('cart_id'))
    if created:
        request.session['cart_id'] = cart.id
    return cart

def home(request):
    categories = Category.objects.all()
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

    context = {
        'categories': categories,
        'items': items,
        'cart_count': cart_count,
        'search_query': search_query
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

from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
import os

def generate_quotation(request):
    cart_id = request.session.get('cart_id')
    if cart_id:
        cart = Cart.objects.get(id=cart_id)
        cart_items = cart.cartitem_set.all()

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'whatsapp_number': '+260772447190'
        }

        # Generate quotation HTML
        html_content = render_to_string('quotation_template.html', context)

        # Generate PDF
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        HTML(string=html_content).write_pdf(pdf_file.name)
        pdf_file.close()

        # Save the PDF to a permanent location (e.g., media directory)
        pdf_path = os.path.join('media', 'quotations', f'quotation_{cart_id}.pdf')
        os.rename(pdf_file.name, pdf_path)

        # Create WhatsApp message
        items_list = "\n".join([f"{item.quantity}x {item.item.name}" for item in cart_items])
        pdf_url = request.build_absolute_uri(reverse('download_quotation', args=[cart_id]))
        whatsapp_message = f"New Order:\n{items_list}\nTotal: K{cart.total_amount}\nDownload PDF: {pdf_url}"
        whatsapp_url = f"https://wa.me/260772447190?text={whatsapp_message}"

        return JsonResponse({
            'success': True,
            'whatsapp_url': whatsapp_url,
            'pdf_url': pdf_url
        })
    return JsonResponse({'success': False})

def download_quotation(request, cart_id):
    pdf_path = os.path.join('media', 'quotations', f'quotation_{cart_id}.pdf')
    with open(pdf_path, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=quotation_{cart_id}.pdf'
        return response