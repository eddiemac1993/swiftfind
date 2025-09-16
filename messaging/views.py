# messaging/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message, Notification
from directory.models import Business
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST


User = get_user_model()

@login_required
@require_POST
def clear_pending_order(request):
    if 'pending_order' in request.session:
        del request.session['pending_order']
        request.session.modified = True
    return JsonResponse({'status': 'success'})

@login_required
def start_conversation(request, business_id):
    business = get_object_or_404(Business, id=business_id)

    # Prevent users from messaging themselves
    if request.user == business.owner:
        return redirect('messaging:conversation_list')

    # Find existing conversation or create a new one
    conversation = Conversation.objects.filter(
        participants=request.user,
        business=business
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(business=business)
        conversation.participants.add(request.user, business.owner)

    # Handle order submission via POST
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        customer_notes = request.POST.get('customer_notes', '').strip()

        if order_id:
            try:
                # Import your Order model (make sure to add the import at the top)
                from pos_system.models import Order

                # Get the order
                order = Order.objects.get(id=order_id, customer=request.user)

                # Mark order as submitted
                order.status = 'submitted'
                order.submitted_at = timezone.now()
                order.save()

                # Generate the order message automatically
                message_content = generate_order_message(order, customer_notes)

                # Create the message in the conversation
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=message_content
                )

                # Create notification for the business owner
                Notification.objects.create(
                    user=business.owner,
                    message=message,
                    is_read=False
                )

                # Clear any pending order from session
                if 'pending_order' in request.session:
                    del request.session['pending_order']
                    request.session.modified = True

            except Order.DoesNotExist:
                # Handle case where order doesn't exist or doesn't belong to user
                pass

    return redirect('messaging:conversation_detail', conversation_id=conversation.id)

from django.template.loader import render_to_string
from django.utils import timezone

def generate_order_message(order, customer_notes):
    """Generate order confirmation message automatically"""
    context = {
        'order': order,
        'business_name': order.business.name,
        'customer_notes': customer_notes,
        'current_date': timezone.now().strftime("%b %d, %Y %H:%M")
    }

    # Simple text version (you can make this more complex if needed)
    message_lines = [
        f"Hello {order.business.name},\n\n",
        f"I would like to confirm my order #{order.id}:\n\n",
        f"*Customer Name:* {order.customer_name}\n",
        f"*Phone:* {order.customer_phone}\n\n",
    ]

    if customer_notes:
        message_lines.append(f"*Additional Notes:* {customer_notes}\n\n")

    message_lines.append("*Order Details:*\n")

    for item in order.items.all():
        item_total = item.quantity * item.price
        message_lines.append(f"- {item.product_name} ({item.quantity} × ZMW {item.price:.2f}) = ZMW {item_total:.2f}\n")

    message_lines.extend([
        f"\n*Subtotal:* ZMW {order.subtotal:.2f}\n",
        f"*Service Fee:* ZMW {order.delivery_fee:.2f}\n",
        f"*Total:* ZMW {order.total:.2f}\n\n",
        "Please confirm this order. Thank you!"
    ])

    return ''.join(message_lines)

@login_required
def conversation_list(request):
    conversations = Conversation.objects.filter(
        participants=request.user
    ).order_by('-updated_at')

    for conv in conversations:
        conv.display_name = conv.get_display_name(request.user)
        conv.unread_count = conv.messages.filter(read=False).exclude(sender=request.user).count()

    return render(request, 'messaging/conversations.html', {
        'conversations': conversations
    })

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    # Mark messages as read when viewing conversation
    conversation.messages.filter(read=False).exclude(sender=request.user).update(read=True)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )

            # Create notifications for all other participants
            for participant in conversation.participants.exclude(id=request.user.id):
                Notification.objects.create(
                    user=participant,
                    message=message,
                    is_read=False
                )

            conversation.save()
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)

    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'display_name': conversation.get_display_name(request.user),
        'messages': conversation.messages.all().order_by('timestamp'),
        'current_user_id': request.user.id,
    })


@login_required
def unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)