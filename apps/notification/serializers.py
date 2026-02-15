from rest_framework import serializers
from .models import Notification, FCMToken, UserNotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'data', 'sent_at', 'created_at']
        read_only_fields = ['id', 'sent_at', 'created_at']

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['id', 'token', 'device_type', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_device_type(self, value):
        if value not in ['ios', 'android']:
            raise serializers.ValidationError("Device type must be 'ios' or 'android'")
        return value

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPreference
        fields = ['push_enabled', 'email_enabled', 'sms_enabled']

class SendNotificationSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField())
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    notification_types = serializers.ListField(
        child=serializers.ChoiceField(choices=['push', 'in_app', 'email', 'sms']),
        default=['push', 'in_app']
    )
    data = serializers.JSONField(required=False, default=dict)


from rest_framework import serializers
from django.utils import timezone
from .models import ScheduledNotification, Notification


class ScheduledNotificationSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    target_user_count = serializers.SerializerMethodField()
    is_due = serializers.SerializerMethodField()
    time_until_scheduled = serializers.SerializerMethodField()

    class Meta:
        model = ScheduledNotification
        fields = [
            'id', 'title', 'message', 'notification_types',
            'scheduled_at', 'created_by', 'created_by_email',
            'recipient_type', 'status', 'sent_at', 'sent_count',
            'failed_count', 'data', 'created_at', 'updated_at',
            'target_user_count', 'is_due', 'time_until_scheduled'
        ]
        read_only_fields = ['sent_at', 'sent_count', 'failed_count']

    def get_target_user_count(self, obj):
        """Get count of users who will receive this notification"""
        return obj.get_target_users().count()

    def get_is_due(self, obj):
        """Check if notification is due to be sent"""
        return obj.is_due()

    def get_time_until_scheduled(self, obj):
        """Get time remaining until scheduled time"""
        now = timezone.now()
        if obj.scheduled_at > now:
            diff = obj.scheduled_at - now
            total_seconds = int(diff.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60

            if days > 0:
                return f"{days} days, {hours} hours"
            elif hours > 0:
                return f"{hours} hours, {minutes} minutes"
            else:
                return f"{minutes} minutes"
        return "Overdue" if obj.status == 'pending' else "Completed"
