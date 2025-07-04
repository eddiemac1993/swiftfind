from django.utils import timezone
from django.contrib.sessions.models import Session
from .models import PageVisit
import logging

logger = logging.getLogger(__name__)

class PageVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip tracking for certain paths
        if self._should_skip_tracking(request.path):
            return self.get_response(request)
        
        try:
            # Get or create session for anonymous users
            session = None
            if hasattr(request, 'session') and request.session.session_key:
                session, _ = Session.objects.get_or_create(
                    session_key=request.session.session_key,
                    defaults={
                        'expire_date': request.session.get_expiry_date()
                    }
                )
            
            # Get user agent from headers
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            logger.debug(f"Tracking visit with user agent: {user_agent}")
            
            PageVisit.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session=session,
                path=request.path,
                method=request.method,
                ip_address=self.get_client_ip(request),
                referrer=request.META.get('HTTP_REFERER'),
                user_agent=user_agent,
                is_authenticated=request.user.is_authenticated
            )
        except Exception as e:
            logger.error(f"Error tracking page visit: {str(e)}")
        
        return self.get_response(request)

    def _should_skip_tracking(self, path):
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt'
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip