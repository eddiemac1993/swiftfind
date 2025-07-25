def notifications(request):
    if not request.user.is_authenticated:
        return {'notification_count': 0}
    
    count = 0
    if hasattr(request.user, 'business'):
        # Count products
        count += request.user.business.businesspost_set.count()
        # Add other notification counts here
        # count += request.user.business.pending_reviews.count()
        # etc.
    
    return {'notification_count': count}