# pos_system/management/commands/link_existing_orders.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pos_system.models import Order

class Command(BaseCommand):
    help = 'Link existing orders to user accounts based on email matching'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be linked without actually saving changes',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find orders without linked users but with email addresses
        unlinked_orders = Order.objects.filter(customer__isnull=True).exclude(customer_email__isnull=True).exclude(customer_email='')
        
        self.stdout.write(f"Found {unlinked_orders.count()} unlinked orders")
        
        linked_count = 0
        for order in unlinked_orders:
            try:
                # Try to find user by email (case-insensitive)
                user = User.objects.get(email__iexact=order.customer_email)
                
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Would link order {order.id} "
                        f"(Customer: '{order.customer_name}', Email: '{order.customer_email}') "
                        f"to user {user.username} ({user.email})"
                    )
                else:
                    order.customer = user
                    order.save()
                    linked_count += 1
                    self.stdout.write(
                        f"Linked order {order.id} "
                        f"(Customer: '{order.customer_name}', Email: '{order.customer_email}') "
                        f"to user {user.username}"
                    )
                    
            except User.DoesNotExist:
                self.stdout.write(
                    f"No user found for order {order.id} "
                    f"with email '{order.customer_email}' and customer name '{order.customer_name}'"
                )
            except User.MultipleObjectsReturned:
                users = User.objects.filter(email__iexact=order.customer_email)
                self.stdout.write(
                    f"Multiple users found for order {order.id} with email '{order.customer_email}': "
                    f"{', '.join([u.username for u in users])}"
                )
        
        if dry_run:
            self.stdout.write(f"[DRY RUN] Would have linked {linked_count} orders")
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully linked {linked_count} orders"))