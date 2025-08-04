# pos_system/utils.py
from decimal import Decimal

def calculate_delivery_fee(product, quantity):
    """
    Calculate delivery fee based on:
    - Fixed K30 fee
    - 5% of (quantity × product price)
    """
    if not product.has_delivery:
        return Decimal('0.00')
    
    fixed_fee = product.delivery_fee
    percentage_fee = (Decimal(quantity) * product.price) * (product.delivery_percentage / Decimal('100.00'))
    return fixed_fee + percentage_fee