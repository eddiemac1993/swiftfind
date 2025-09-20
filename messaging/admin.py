from django.contrib import admin
from django.contrib.auth import get_user_model
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from .models import Conversation, Message
from directory.models import Business

User = get_user_model()

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'timestamp', 'read', 'preview_content')
    fields = ('sender', 'preview_content', 'timestamp', 'read')
    
    def preview_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    preview_content.short_description = 'Content Preview'

class ConversationForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('Participants', False)
    )
    
    class Meta:
        model = Conversation
        fields = '__all__'

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    form = ConversationForm
    list_display = ('id', 'business', 'participants_list', 'created_at', 'updated_at', 'message_count', 'unread_count')
    list_filter = ('business', 'created_at', 'updated_at')
    search_fields = ('business__name', 'participants__username')
    inlines = [MessageInline]
    actions = ['send_bulk_message']
    change_list_template = 'admin/messaging/conversation/change_list.html'
    
    def participants_list(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    participants_list.short_description = 'Participants'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def unread_count(self, obj):
        return sum([obj.get_unread_count(user) for user in obj.participants.all()])
    unread_count.short_description = 'Total Unread'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('send-bulk-message/',
                self.admin_site.admin_view(self.send_bulk_message_view),
                name='messaging_conversation_send_bulk_message'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['bulk_message_url'] = reverse('admin:messaging_conversation_send_bulk_message')
        return super().changelist_view(request, extra_context=extra_context)
    
    def send_bulk_message_view(self, request):
        if request.method == 'POST':
            user_ids = request.POST.getlist('users')
            content = request.POST.get('content', '')
            
            if not user_ids or not content:
                messages.error(request, "Please select users and provide message content")
                return redirect('admin:messaging_conversation_send_bulk_message')
                
            users = User.objects.filter(id__in=user_ids)
            success_count = 0
            
            for user in users:
                admin_user = request.user
                business = Business.objects.first()
                if not business:
                    business = Business.objects.create(
                        name="Default Business", 
                        owner=admin_user,
                        description="Automatically created for messaging"
                    )
                
                # Try to find an existing conversation with exactly these participants
                # Try to find a direct 1-to-1 conversation between admin and user, regardless of business
                existing_conversations = Conversation.objects.filter(participants=admin_user).filter(participants=user).distinct()
                
                conversation = None
                for conv in existing_conversations:
                    if conv.participants.count() == 2:
                        conversation = conv
                        break
                
                # If not found, create a new one with a neutral business
                if not conversation:
                    business, _ = Business.objects.get_or_create(
                        name="Admin Messaging", 
                        defaults={
                            'owner': admin_user,
                            'description': 'Used for admin-to-user bulk messaging'
                        }
                    )
                    conversation = Conversation.objects.create(business=business, created_at=timezone.now())
                    conversation.participants.set([admin_user, user])


                
                Message.objects.create(
                    conversation=conversation,
                    sender=admin_user,
                    content=content,
                    read=False
                )
                success_count += 1
                
            messages.success(request, f"Message sent successfully to {success_count} users")
            return redirect('admin:messaging_conversation_changelist')
            
        context = {
            'title': 'Send Message to Multiple Users',
            'users': User.objects.all().order_by('username'),
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/messaging/bulk_message.html', context)
    
    def send_bulk_message(self, request, queryset):
        return HttpResponseRedirect(
            reverse('admin:messaging_conversation_send_bulk_message')
        )
    send_bulk_message.short_description = "Send message to multiple users"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation_link', 'sender', 'preview_content', 'timestamp', 'read_status')
    list_filter = ('read', 'timestamp', 'sender')
    search_fields = ('content', 'sender__username', 'conversation__business__name')
    readonly_fields = ('timestamp',)
    actions = ['mark_as_read', 'mark_as_unread']
    
    def conversation_link(self, obj):
        url = reverse('admin:messaging_conversation_change', args=[obj.conversation.id])
        return format_html('<a href="{}">Conversation #{}</a>', url, obj.conversation.id)
    conversation_link.short_description = 'Conversation'
    
    def preview_content(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    preview_content.short_description = 'Content'
    
    def read_status(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.read else 'red',
            '✔️ Read' if obj.read else '✖️ Unread'
        )
    read_status.short_description = 'Status'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(read=True)
        self.message_user(request, f"{updated} messages marked as read")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(read=False)
        self.message_user(request, f"{updated} messages marked as unread")
    mark_as_unread.short_description = "Mark selected messages as unread"