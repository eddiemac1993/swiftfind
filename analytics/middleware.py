from django.utils import timezone
from django.contrib.sessions.models import Session
from .models import PageVisit

class PageVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip admin pages if desired
        if not request.path.startswith('/admin/'):
            # Get or create session for anonymous users
            session = None
            if hasattr(request, 'session') and request.session.session_key:
                session, _ = Session.objects.get_or_create(
                    session_key=request.session.session_key
                )
            
            PageVisit.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session=session,
                path=request.path,
                method=request.method,
                ip_address=self.get_client_ip(request),
                referrer=request.META.get('HTTP_REFERER'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                is_authenticated=request.user.is_authenticated
            )
        
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip