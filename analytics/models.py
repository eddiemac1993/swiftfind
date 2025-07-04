from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django_user_agents.utils import get_user_agent
import logging

logger = logging.getLogger(__name__)

class PageVisit(models.Model):
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    session = models.ForeignKey(
        Session, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    ip_address = models.GenericIPAddressField()
    referrer = models.TextField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_authenticated = models.BooleanField(default=False)

    @property
    def device_info(self):
        default_info = {
            'device': 'Unknown',
            'os': 'Unknown',
            'browser': 'Unknown',
            'is_mobile': False,
            'is_tablet': False,
            'is_pc': False,
            'is_bot': False
        }
        
        if not self.user_agent:
            return default_info
            
        try:
            # Parse user agent
            ua = get_user_agent(self.user_agent)
            
            # Handle case where parsing failed
            if not hasattr(ua, 'device'):
                logger.warning(f"Failed to parse user agent: {self.user_agent}")
                return default_info
                
            return {
                'device': getattr(ua.device, 'family', 'Unknown'),
                'os': self._clean_os_version(getattr(ua.os, 'family', 'Unknown'), 
                                           getattr(ua.os, 'version_string', '')),
                'browser': self._clean_browser_version(getattr(ua.browser, 'family', 'Unknown'),
                                                     getattr(ua.browser, 'version_string', '')),
                'is_mobile': ua.is_mobile,
                'is_tablet': ua.is_tablet,
                'is_pc': ua.is_pc,
                'is_bot': ua.is_bot or self._is_bot_user_agent(self.user_agent)
            }
        except Exception as e:
            logger.error(f"Error parsing device info: {str(e)}")
            return default_info
    
    def _clean_os_version(self, os_family, version):
        version = version or ''
        return f"{os_family} {version}".strip()
    
    def _clean_browser_version(self, browser_family, version):
        version = version or ''
        return f"{browser_family} {version}".strip()
    
    def _is_bot_user_agent(self, user_agent):
        bot_indicators = ['bot', 'crawler', 'spider', 'facebook', 'slurp', 'bing']
        return any(indicator in user_agent.lower() for indicator in bot_indicators)

    def __str__(self):
        return f"{self.path} - {self.timestamp}"