import logging
from django.utils import timezone
from apps.notification.models import Notification
from apps.accounts.models import User
from apps.notification.tasks import send_push_notification, send_email_notification

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_notification(user_id, title, message, notification_types=['push', 'in_app'], data=None):
        """The one method to rule them all"""
        user = User.objects.get(id=user_id)
        preferences = getattr(user, 'notification_preference', None)
        
        for notif_type in notification_types:
            if NotificationService._should_send(user, notif_type, preferences):
                NotificationService._dispatch_notification(
                    user, title, message, notif_type, data
                )
    
    @staticmethod
    def _should_send(user, notif_type, preferences):
        if not preferences:
            return True
        return getattr(preferences, f'{notif_type}_enabled', True)
    
    @staticmethod
    def _dispatch_notification(user, title, message, notif_type, data):
        # Create notification record
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notif_type,
            data=data or {}
        )
        
        if notif_type == 'push':
            send_push_notification.delay(notification.id)
        elif notif_type == 'in_app':
            # In-app notifications are stored in DB and available via API; mark as sent
            notification.sent_at = timezone.now()
            notification.save()
        elif notif_type == 'email':
            send_email_notification.delay(notification.id)