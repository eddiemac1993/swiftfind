# management/commands/assign_verification_permission.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from directory.models import Business

class Command(BaseCommand):
    help = 'Assign business verification permission to users'

    def add_arguments(self, parser):
        parser.add_argument('usernames', nargs='+', type=str, help='Usernames to assign permission to')

    def handle(self, *args, **options):
        content_type = ContentType.objects.get_for_model(Business)
        try:
            permission = Permission.objects.get(
                codename='can_verify',
                content_type=content_type,
            )
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR("Permission 'can_verify' not found. Did you run makemigrations & migrate?"))
            return
        
        for username in options['usernames']:
            try:
                user = User.objects.get(username=username)
                user.user_permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Successfully assigned 'can_verify' permission to {username}")
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ User {username} does not exist")
                )
