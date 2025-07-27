from .models import Message, Conversation

def unread_messages(request):
    if request.user.is_authenticated:
        return {
            'unread_count': Message.objects.filter(
                conversation__participants=request.user,
                read=False
            ).exclude(sender=request.user).count(),
            'is_business_owner': hasattr(request.user, 'owned_businesses') and request.user.owned_businesses.exists()
        }
    return {}