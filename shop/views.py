from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Shop, Request, Payment, Balance, Category, Cart, CartItem, Item, RequestItem
from .forms import ShopForm, RequestForm, PaymentForm

@login_required
def profile(request):
    # Get the shop associated with the logged-in user
    shop = Shop.objects.get(user=request.user)

    # Get or create the balance for the shop
    balance, created = Balance.objects.get_or_create(shop=shop, defaults={
        'total_amount': 0,
        'amount_paid': 0,
        'amount_due': 0,
    })

    # Pass the balance and shop details to the template
    context = {
        'shop': shop,
        'balance': balance,
    }
    return render(request, 'profile.html', context)

# Item List Page
def item_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    items = Item.objects.all()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        items = items.filter(category=category)

    return render(request, 'item_list.html', {
        'category': category,
        'categories': categories,
        'items': items,
    })

# Add to Cart
@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('item_list')

# View Cart
@login_required
def view_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    return render(request, 'view_cart.html', {'cart': cart})

# Update Cart Quantities
@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Quantity updated successfully.')
        else:
            messages.error(request, 'Quantity must be at least 1.')
    return redirect('view_cart')

# Remove Item from Cart
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('view_cart')

# View Request Page
@login_required
def view_request(request):
    cart = get_object_or_404(Cart, user=request.user)
    return render(request, 'view_request.html', {'cart': cart})

# Download Request as PDF
@login_required
def download_request_pdf(request):
    cart = get_object_or_404(Cart, user=request.user)

    # Render the request details to HTML
    html_string = render_to_string('request_pdf.html', {'cart': cart})

    # Generate the PDF
    pdf_file = HTML(string=html_string).write_pdf()

    # Return the PDF as a response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="request_{cart.id}.pdf"'
    return response

# Create Request (Optional)
@login_required
def create_request(request):
    # Get the shop associated with the logged-in user
    shop = Shop.objects.get(user=request.user)

    if request.method == 'POST':
        form = RequestForm(request.POST, shop=shop)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.shop = shop
            request_obj.save()
            return redirect('request_detail', pk=request_obj.pk)  # Pass the primary key
    else:
        form = RequestForm(shop=shop)

    return render(request, 'create_request.html', {'form': form})

# Request Detail (Optional)
def request_detail(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    return render(request, 'request_detail.html', {'request_obj': request_obj})

# Make Payment (Optional)
def make_payment(request, request_id):
    request_obj = Request.objects.get(id=request_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST, request=request_obj)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.request = request_obj
            payment.save()
            balance = Balance.objects.get(shop=request_obj.shop)
            balance.make_payment(payment.amount_paid, payment.payment_type)
            return redirect('payment_detail')
    else:
        form = PaymentForm(request=request_obj)
    return render(request, 'make_payment.html', {'form': form})