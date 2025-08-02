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

    # Check for pending order in POST data
    if request.method == 'POST' and 'pending_order' in request.POST:
        request.session['pending_order'] = request.POST['pending_order']
        request.session.modified = True

    return redirect('messaging:conversation_detail', conversation_id=conversation.id)

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