# auth_backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .models import BusinessMember

User = get_user_model()

class BusinessAuthBackend(BaseBackend):
    def authenticate(self, request, business_username=None, business_password=None, **kwargs):
        try:
            business_member = BusinessMember.objects.get(business_username=business_username)
            if business_member.check_password(business_password) and business_member.is_active:
                return business_member.user
        except BusinessMember.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None