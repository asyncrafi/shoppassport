from django.db import models
from django.utils import timezone
from apps.accounts.models import User

class ScheduledNotification(models.Model):
    RECIPIENT_CHOICES = (
        ('all', 'All Users'),
        ('specific', 'Specific Users'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_types = models.JSONField(default=list)  # ['push', 'email', 'in_app']
    
    # Scheduling
    scheduled_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_schedules')
    
    # Recipients
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_CHOICES, default='all')
    specific_users = models.ManyToManyField(User, blank=True, related_name='scheduled_notifications')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    # Extra data
    data = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_at']
    
    def __str__(self):
        return f"Scheduled: {self.title} - {self.scheduled_at}"
    
    def is_due(self):
        """Check if notification is due to be sent"""
        return timezone.now() >= self.scheduled_at and self.status == 'pending'
    
    def get_target_users(self):
        """Get users who should receive this notification"""
        if self.recipient_type == 'all':
            return User.objects.filter(is_active=True)
        else:
            return self.specific_users.filter(is_active=True)


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
        ('email', 'Email Notification'),
        ('sms', 'SMS Notification'),
    )
    scheduled_notification = models.ForeignKey(
        ScheduledNotification,
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sent_notifications'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='push', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    data = models.JSONField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True) 

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notification', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        user_email = self.user.email if self.user else "No User"
        return f"{user_email} - {self.title} ({self.notification_type})"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()

    def mark_as_sent(self):
        """Mark notification as sent"""
        self.is_sent = timezone.now()
        self.save()

class UserNotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference', blank=True, null=True)
    push_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=False)
    sms_enabled = models.BooleanField(default=False)
    in_app_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_email = self.user.email if self.user else "No User"
        return f"{user_email} - Preferences"
    
    class Meta:
        verbose_name_plural = "User Notification Preferences"

class FCMToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_tokens', blank=True, null=True)
    token = models.CharField(max_length=255, unique=True, blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)  # e.g. 'android', 'ios'
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_email = self.user.email if self.user else "No User"
        token_display = self.token or "No Token"
        return f"{user_email} - {token_display}"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'token')