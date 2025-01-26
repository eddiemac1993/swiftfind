from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Sale, Order
from directory.models import Business
from .forms import ProductForm, SaleForm
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

@login_required
def product_list(request):
    business = get_object_or_404(Business, owner=request.user)
    products = Product.objects.filter(business=business)
    cart = request.session.get('cart', {})
    cart_total_items = sum(cart.values())
    return render(request, 'pos/product_list.html', {
        'products': products,
        'cart_total_items': cart_total_items,
    })

@login_required
def add_product(request):
    business = get_object_or_404(Business, owner=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.business = business
            product.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'pos/add_product.html', {'form': form})

@login_required
def process_sale(request):
    business = get_object_or_404(Business, owner=request.user)
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('view_cart')  # Redirect if cart is empty

    # Create a new order for the business
    order = Order.objects.create(business=business)

    # Process each item in the cart
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id, business=business)
        if product.stock_quantity >= quantity:
            Sale.objects.create(
                business=business,
                order=order,
                product=product,
                quantity=quantity,
                total_price=product.price * quantity
            )
            product.stock_quantity -= quantity
            product.save()
        else:
            # Handle insufficient stock
            return render(request, 'pos/error.html', {'message': f'Not enough stock for {product.name}'})

    # Clear the cart
    if 'cart' in request.session:
        del request.session['cart']

    # Redirect to the receipt page with the order_id
    return redirect('receipt', order_id=order.id)

@login_required
def receipt(request, order_id):
    business = get_object_or_404(Business, owner=request.user)
    order = get_object_or_404(Order, id=order_id, business=business)
    sales = order.sales.all()  # Fetch all sales linked to this order
    return render(request, 'pos/receipt.html', {'order': order, 'sales': sales})


@login_required
def receipt_pdf(request, order_id):
    business = get_object_or_404(Business, owner=request.user)
    order = get_object_or_404(Order, id=order_id, business=business)
    sales = order.sales.all()  # Fetch all sales linked to this order
    html_string = render_to_string('pos/receipt.html', {'order': order, 'sales': sales})
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{order.order_number}.pdf"'
    return response

@login_required
def add_to_cart(request, product_id):
    business = get_object_or_404(Business, owner=request.user)
    product = get_object_or_404(Product, id=product_id, business=business)
    cart = request.session.get('cart', {})

    quantity = int(request.POST.get('quantity', 1))
    if product.id in cart:
        cart[product.id] += quantity
    else:
        cart[product.id] = quantity

    request.session['cart'] = cart
    return redirect('product_list')

@login_required
def view_cart(request):
    business = get_object_or_404(Business, owner=request.user)
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys(), business=business)
    cart_items = []
    total_amount = 0

    for product in products:
        quantity = cart[str(product.id)]
        total_price = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': total_price,
        })
        total_amount += total_price

    return render(request, 'pos/view_cart.html', {'cart_items': cart_items, 'total_amount': total_amount})

def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
    return redirect('product_list')

