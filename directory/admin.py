from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group, Permission
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter, DropdownFilter
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from django.utils import timezone
from .models import (
    NewsFeed, Comment, Advertisement, Category,
    BusinessRole, BusinessDepartment, Business,
    BusinessMember, BusinessPost, Review,
    BusinessImage, ChatRoom, ChatMessage,
    SearchQuery, UserProfile
)

# ======================
# RESOURCE CLASSES FOR IMPORT/EXPORT
# ======================
class BusinessResource(resources.ModelResource):
    class Meta:
        model = Business
        fields = ('id', 'name', 'owner__username', 'category__name', 'address', 'phone_number', 'email', 'status')
        export_order = fields

class ReviewResource(resources.ModelResource):
    class Meta:
        model = Review
        fields = ('id', 'business__name', 'user__username', 'rating', 'title', 'status', 'created_at')
        export_order = fields

# ======================
# INLINE ADMIN CLASSES
# ======================
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('user', 'content', 'created_at', 'is_approved')
    fields = ('user', 'content', 'created_at', 'is_approved')
    can_delete = False

class BusinessPostInline(admin.TabularInline):
    model = BusinessPost
    extra = 0
    fields = ('title', 'post_type', 'image_preview', 'is_featured', 'created_at')
    readonly_fields = ('created_at', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'

class BusinessImageInline(admin.TabularInline):
    model = BusinessImage
    extra = 0
    fields = ('image', 'thumbnail_preview', 'caption')
    readonly_fields = ('thumbnail_preview',)

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="50" />', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = 'Thumbnail'

class BusinessMemberInline(admin.TabularInline):
    model = BusinessMember
    extra = 0
    fields = ('user', 'role', 'business_username', 'is_active', 'position')
    raw_id_fields = ('user',)

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ('user', 'rating', 'title', 'status', 'created_at')
    readonly_fields = ('created_at',)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ('primary_business', 'phone_number', 'address', 'profile_picture', 'bio')
    raw_id_fields = ('primary_business',)

# ======================
# CUSTOM USER ADMIN
# ======================
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'business_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    actions = ['activate_users', 'deactivate_users']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(_business_count=Count('business_memberships'))
        return qs

    def business_count(self, obj):
        return obj._business_count
    business_count.admin_order_field = '_business_count'
    business_count.short_description = 'Business Memberships'

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} users were activated.")
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} users were deactivated.")
    deactivate_users.short_description = "Deactivate selected users"

# ======================
# MAIN MODEL ADMIN CLASSES
# ======================
@admin.register(NewsFeed)
class NewsFeedAdmin(ImportExportModelAdmin):
    list_display = ('title', 'category', 'created_at', 'updated_at', 'comment_count')
    list_filter = ('category', ('created_at', DateRangeFilter))
    search_fields = ('title', 'content')
    inlines = [CommentInline]
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'category', 'content')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(_comment_count=Count('comments'))
        return qs

    def comment_count(self, obj):
        return obj._comment_count
    comment_count.admin_order_field = '_comment_count'
    comment_count.short_description = 'Comments'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('truncated_content', 'newsfeed', 'user', 'created_at', 'is_approved')
    list_filter = ('is_approved', ('created_at', DateRangeFilter))
    search_fields = ('content', 'newsfeed__title', 'user__username')
    list_editable = ('is_approved',)
    actions = ['approve_comments', 'disapprove_comments']

    def truncated_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    truncated_content.short_description = 'Content'

    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comments were approved.")
    approve_comments.short_description = "Approve selected comments"

    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} comments were disapproved.")
    disapprove_comments.short_description = "Disapprove selected comments"

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'slot', 'is_active', 'start_time', 'end_time', 'is_running', 'days_remaining')
    list_filter = ('is_active', 'slot', ('start_time', DateTimeRangeFilter), ('end_time', DateTimeRangeFilter))
    search_fields = ('title', 'small_text')
    list_editable = ('is_active', 'slot')
    readonly_fields = ('is_running',)
    fieldsets = (
        (None, {
            'fields': ('title', 'small_text', 'slot', 'is_active')
        }),
        ('Media', {
            'fields': ('image', 'link')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'is_running')
        }),
    )

    def days_remaining(self, obj):
        if obj.end_time:
            delta = obj.end_time - timezone.now()
            return delta.days
        return None
    days_remaining.short_description = 'Days Left'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'business_count')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(_business_count=Count('business'))
        return qs

    def business_count(self, obj):
        return obj._business_count
    business_count.admin_order_field = '_business_count'
    business_count.short_description = 'Businesses'

@admin.register(BusinessRole)
class BusinessRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default', 'permission_count')
    list_filter = ('is_default',)
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)

    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Permissions'

@admin.register(BusinessDepartment)
class BusinessDepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_department', 'business_count')
    list_filter = (('parent_department', RelatedDropdownFilter),)
    search_fields = ('name', 'description')

    def business_count(self, obj):
        return obj.businesses.count()
    business_count.short_description = 'Businesses'

@admin.register(Business)
class BusinessAdmin(ImportExportModelAdmin):
    resource_class = BusinessResource
    list_display = ('name', 'owner', 'category', 'city', 'status', 'average_rating',
                   'review_count', 'member_count', 'image_count', 'post_image_count', 'is_admin_added', 'logo_preview')
    list_filter = (
        'status',
        'is_admin_added',
        ('category', RelatedDropdownFilter),
        ('owner', RelatedDropdownFilter),
        ('city', DropdownFilter),
        ('created_at', DateRangeFilter),
    )
    search_fields = ('name', 'description', 'address', 'phone_number', 'email')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [BusinessPostInline, BusinessImageInline, BusinessMemberInline, ReviewInline]
    readonly_fields = ('average_rating', 'created_at', 'updated_at', 'logo_preview')
    filter_horizontal = ('default_roles', 'departments')
    date_hierarchy = 'created_at'
    raw_id_fields = ('owner',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'owner', 'category', 'status')
        }),
        ('Details', {
            'fields': ('description', 'tags', 'address', 'phone_number', 'email', 'website', 'city')
        }),
        ('Media', {
            'fields': ('logo', 'logo_preview', 'company_profile')
        }),
        ('Organization', {
            'fields': ('default_roles', 'departments')
        }),
        ('Metadata', {
            'fields': ('is_admin_added', 'created_at', 'updated_at', 'average_rating'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_active', 'mark_as_inactive', 'export_as_csv']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            _review_count=Count('reviews'),
            _member_count=Count('members'),
            _image_count=Count('images'),
            _post_image_count=Count('posts__image', distinct=True)
        )
        return qs

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "-"
    logo_preview.short_description = 'Logo'

    def review_count(self, obj):
        return obj._review_count
    review_count.admin_order_field = '_review_count'
    review_count.short_description = 'Reviews'

    def member_count(self, obj):
        return obj._member_count
    member_count.admin_order_field = '_member_count'
    member_count.short_description = 'Members'

    def image_count(self, obj):
        url = reverse('admin:directory_businessimage_changelist') + f'?business__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, obj._image_count)
    image_count.admin_order_field = '_image_count'
    image_count.short_description = 'Images'

    def post_image_count(self, obj):
        url = reverse('admin:directory_businesspost_changelist') + f'?business__id__exact={obj.id}&image__isnull=False'
        return format_html('<a href="{}">{}</a>', url, obj._post_image_count)
    post_image_count.admin_order_field = '_post_image_count'
    post_image_count.short_description = 'Post Images'

    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f"{updated} businesses were marked as active.")
    mark_as_active.short_description = "Mark selected as active"

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f"{updated} businesses were marked as inactive.")
    mark_as_inactive.short_description = "Mark selected as inactive"

@admin.register(BusinessMember)
class BusinessMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'business', 'role', 'is_active', 'last_login')
    list_filter = (
        'is_active',
        ('role', RelatedDropdownFilter),
        ('business', RelatedDropdownFilter),
        ('last_login', DateRangeFilter),
    )
    search_fields = ('user__username', 'business__name', 'role__name', 'business_username')
    raw_id_fields = ('user', 'business')
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        (None, {
            'fields': ('user', 'business', 'role', 'is_active')
        }),
        ('Credentials', {
            'fields': ('business_username', 'business_password'),
            'classes': ('collapse',)
        }),
        ('Profile', {
            'fields': ('employee_id', 'department', 'position')
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    actions = ['activate_members', 'deactivate_members']

    def activate_members(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} members were activated.")
    activate_members.short_description = "Activate selected members"

    def deactivate_members(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} members were deactivated.")
    deactivate_members.short_description = "Deactivate selected members"

@admin.register(BusinessPost)
class BusinessPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'post_type', 'is_featured', 'created_at', 'price', 'image_preview')
    list_filter = (
        'post_type',
        'is_featured',
        ('business', RelatedDropdownFilter),
        ('created_at', DateRangeFilter),
    )
    search_fields = ('title', 'content', 'business__name')
    list_editable = ('is_featured',)
    raw_id_fields = ('business',)
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    fieldsets = (
        (None, {
            'fields': ('business', 'title', 'post_type', 'content', 'is_featured')
        }),
        ('Media', {
            'fields': ('image', 'image_preview', 'price')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image'

@admin.register(Review)
class ReviewAdmin(ImportExportModelAdmin):
    resource_class = ReviewResource
    list_display = ('business', 'user', 'rating', 'status', 'created_at', 'helpful_votes')
    list_filter = (
        'status',
        'rating',
        ('business', RelatedDropdownFilter),
        ('user', RelatedDropdownFilter),
        ('created_at', DateRangeFilter),
    )
    search_fields = ('title', 'comment', 'business__name', 'user__username')
    list_editable = ('status',)
    raw_id_fields = ('business', 'user')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('business', 'user', 'session_key', 'status')
        }),
        ('Review Content', {
            'fields': ('rating', 'title', 'comment', 'helpful_votes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'slug'),
            'classes': ('collapse',)
        }),
    )
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} reviews were approved.")
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} reviews were rejected.")
    reject_reviews.short_description = "Reject selected reviews"

@admin.register(BusinessImage)
class BusinessImageAdmin(admin.ModelAdmin):
    list_display = ('business', 'caption', 'created_at', 'thumbnail_preview')
    list_filter = (('business', RelatedDropdownFilter), ('created_at', DateRangeFilter))
    search_fields = ('caption', 'business__name')
    raw_id_fields = ('business',)
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview')

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="50" />', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = 'Thumbnail'

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_private', 'created_at', 'message_count')
    list_filter = ('is_private', ('created_at', DateRangeFilter))
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(_message_count=Count('messages'))
        return qs

    def message_count(self, obj):
        return obj._message_count
    message_count.admin_order_field = '_message_count'
    message_count.short_description = 'Messages'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'user_name', 'truncated_message', 'timestamp', 'ip_address')
    list_filter = (('room', RelatedDropdownFilter), ('timestamp', DateRangeFilter))
    search_fields = ('user_name', 'message')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

    def truncated_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    truncated_message.short_description = 'Message'

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'city', 'category', 'timestamp', 'count')
    list_filter = (
        ('city', DropdownFilter),
        ('category', DropdownFilter),
        ('timestamp', DateRangeFilter),
    )
    search_fields = ('query', 'city', 'category')
    readonly_fields = ('timestamp',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'primary_business', 'phone_number', 'profile_picture_preview')
    search_fields = ('user__username', 'phone_number', 'address')
    raw_id_fields = ('user', 'primary_business')
    readonly_fields = ('created_at', 'updated_at', 'profile_picture_preview')

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" />', obj.profile_picture.url)
        return "-"
    profile_picture_preview.short_description = 'Profile Picture'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Optional: Custom Group Admin
class GroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('permissions',)
    search_fields = ('name',)

admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)