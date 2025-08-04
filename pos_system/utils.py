# pos_system/utils.py
from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail

def calculate_delivery_fee(product, quantity):
    """
    Calculate delivery fee based on:
    - Fixed K30 fee
    - 3% of (quantity × product price)
    Returns Decimal with 2 decimal places
    """
    if not getattr(product, 'has_delivery', True):
        return Decimal('0.00')

    fixed_fee = Decimal('30.00')  # K30 base fee
    percentage_fee = (Decimal(quantity) * product.price) * Decimal('0.03')  # 3% of value
    total = fixed_fee + percentage_fee
    
    # Round to 2 decimal places (like currency)
    return total.quantize(Decimal('0.00'))

def send_order_notification(order, to_business=False, to_customer=False):
    """
    Basic email notification for orders
    """
    if to_business:
        subject = f"New Order #{order.order_number}"
        message = (
            f"New order from {order.customer_name}\n"
            f"Phone: {order.customer_phone}\n"
            f"Total: K{order.total:.2f}\n\n"
            f"View order: {settings.SITE_URL}/orders/{order.uuid}/"
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.business.primary_email],
            fail_silently=True
        )

    if to_customer and order.customer_email:
        subject = f"Order Confirmation #{order.order_number}"
        message = (
            f"Thank you for your order from {order.business.name}\n"
            f"Order Total: K{order.total:.2f}\n"
            f"We'll contact you shortly about delivery.\n\n"
            f"Order details: {settings.SITE_URL}/orders/{order.uuid}/"
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer_email],
            fail_silently=True
        )