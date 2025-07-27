from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Conversation, Message
from directory.models import Business
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def conversation_list(request):
    conversations = Conversation.objects.filter(
        participants=request.user
    ).order_by('-updated_at')

    # Add display names and unread counts
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

    # Get appropriate display name
    display_name = conversation.get_display_name(request.user)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            conversation.save()
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)

    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'display_name': display_name,
        'messages': conversation.messages.all().order_by('timestamp')
    })

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

    return redirect('messaging:conversation_detail', conversation_id=conversation.id)