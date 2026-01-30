from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, OTP, UserProfile


class CustomUserAdmin(UserAdmin):
    """Admin configuration for custom User model."""
    
    list_display = ('email', 'name', 'is_active', 'is_staff', 'is_superuser', 
                   'social_auth_provider', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'social_auth_provider',
                   'event_admin', 'shop_admin', 'shopper', 'is_blocked', 'is_deleted')
    search_fields = ('email', 'profile__name', 'username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'social_auth_provider')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Roles'), {
            'fields': ('event_admin', 'shop_admin', 'shopper'),
        }),
        (_('Status'), {
            'fields': ('is_blocked', 'is_deleted', 'deleted_at'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    def name(self, obj):
        return obj.profile.name if hasattr(obj, 'profile') else '-'
    name.short_description = 'Name'
    
    def get_queryset(self, request):
        """Exclude soft-deleted users by default."""
        qs = super().get_queryset(request)
        return qs.filter(is_deleted=False)
    
    actions = ['block_users', 'unblock_users', 'soft_delete_users', 'restore_users']
    
    def block_users(self, request, queryset):
        queryset.update(is_blocked=True)
    block_users.short_description = "Block selected users"
    
    def unblock_users(self, request, queryset):
        queryset.update(is_blocked=False)
    unblock_users.short_description = "Unblock selected users"
    
    def soft_delete_users(self, request, queryset):
        for user in queryset:
            user.soft_delete()
    soft_delete_users.short_description = "Soft delete selected users"
    
    def restore_users(self, request, queryset):
        for user in queryset:
            user.restore()
    restore_users.short_description = "Restore selected users"


class OTPAdmin(admin.ModelAdmin):
    """Admin configuration for OTP model."""
    
    list_display = ('user', 'otp', 'purpose', 'is_used', 'expires_at', 'created_at')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('user__email', 'otp')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'otp', 'purpose')}),
        (_('Status'), {'fields': ('expires_at', 'is_used')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )
    
    actions = ['mark_as_used', 'mark_as_unused']
    
    def mark_as_used(self, request, queryset):
        queryset.update(is_used=True)
    mark_as_used.short_description = "Mark selected OTPs as used"
    
    def mark_as_unused(self, request, queryset):
        queryset.update(is_used=False)
    mark_as_unused.short_description = "Mark selected OTPs as unused"


class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model."""
    
    list_display = ('user', 'name', 'phone', 'gender', 'profile_completed', 'last_active')
    list_filter = ('gender', 'profile_completed')
    search_fields = ('user__email', 'name', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'last_active')
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Personal Information'), {
            'fields': ('name', 'temp_email', 'phone', 'date_of_birth', 'gender')
        }),
        (_('Profile'), {
            'fields': ('bio', 'profile_picture')
        }),
        (_('Status'), {
            'fields': ('profile_completed', 'last_active')
        }),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )
    
    def save_model(self, request, obj, form, change):
        """Update profile_completed status when saving."""
        if obj.name and obj.phone:
            obj.profile_completed = True
        super().save_model(request, obj, form, change)


# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(OTP, OTPAdmin)
admin.site.register(UserProfile, UserProfileAdmin)