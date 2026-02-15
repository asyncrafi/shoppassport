from django.contrib import admin
from .models import Notification, UserNotificationPreference, FCMToken, ScheduledNotification
from django.contrib import admin

@admin.register(ScheduledNotification)
class ScheduledNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'scheduled_at', 'recipient_type', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'recipient_type', 'scheduled_at', 'created_at']
    search_fields = ['title', 'message', 'created_by__username', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'sent_count', 'failed_count']
    filter_horizontal = ['specific_users']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'message', 'notification_types', 'data')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'created_by')
        }),
        ('Recipients', {
            'fields': ('recipient_type', 'specific_users')
        }),
        ('Status Tracking', {
            'fields': ('status', 'sent_at', 'sent_count', 'failed_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'push_enabled', 'email_enabled', 'sms_enabled')
    search_fields = ('user__email',)
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'device_type', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active')
    search_fields = ('user__email', 'token')
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'updated_at')
