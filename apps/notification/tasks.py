from celery import shared_task
from django.utils import timezone
from apps.accounts.models import User
import logging
import firebase_admin
from firebase_admin import credentials
from celery.schedules import crontab
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

from django.conf import settings

_firebase_initialized = False

def _initialize_firebase():
    """Lazy initialization of Firebase - only initialize when actually needed"""
    global _firebase_initialized
    
    if _firebase_initialized:
        return
    
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        _firebase_initialized = True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


@shared_task(bind=True, max_retries=3)
def send_push_notification(self, notification_id):
    try:
        # Lazy initialize Firebase
        _initialize_firebase()
        
        from firebase_admin import messaging
        from .models import Notification, FCMToken

        notification = Notification.objects.get(id=notification_id)
        tokens = FCMToken.objects.filter(
            user=notification.user,
            is_active=True
        ).values_list('token', flat=True)

        logger.info(f"🔥 DEBUGGING - User {notification.user.id} has {len(tokens)} active tokens")

        if not tokens:
            logger.warning(f"No active FCM tokens for user {notification.user.id}")
            return

        # Print tokens for debugging
        for token in tokens:
            logger.info(f"🔥 Token: {token[:50]}...")

        # 🍎 iOS FIX - Add APNs configuration
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.message,
            ),
            data={str(k): str(v) for k, v in notification.data.items()} if notification.data else {
                "type": "notification"},

            # 🍎 APNs configuration for iOS
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=notification.title,
                            body=notification.message,
                        ),
                        badge=1,
                        sound="default",
                        content_available=True
                    )
                ),
                headers={
                    'apns-priority': '10',
                    'apns-push-type': 'alert'
                }
            ),
            tokens=list(tokens),
        )

        logger.info(f"🔥 Sending message with APNs config...")
        response = messaging.send_each_for_multicast(message)
        logger.info(f"🔥 Firebase response - Success: {response.success_count}, Failures: {response.failure_count}")

        # Log individual failures
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    logger.error(f"🔥 Token {idx} failed: {resp.exception}")

        # Handle failed tokens
        _handle_failed_tokens(response, tokens, notification.user)

        # Mark as sent
        notification.sent_at = timezone.now()
        notification.save()

        logger.info(f"🔥 COMPLETE - Push notification sent to {len(tokens)} tokens, {response.failure_count} failures")

    except Exception as exc:
        logger.error(f"🔥 Push notification error: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

# WebSocket notification sending removed — in-app notifications are stored in DB and available via API.


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, notification_id):
    try:
        from apps.core.utils.mailgun_service import MailgunEmailService
        from .models import Notification
        from django.utils import timezone

        notification = Notification.objects.get(id=notification_id)
        mailgun_service = MailgunEmailService()

        mailgun_service.send_transactional_email(
            to_email=notification.user.email,
            to_name=notification.user.profile.name,
            subject=notification.title,
            html_content=f"<p>{notification.message}</p>",
            text_content=notification.message
        )

        notification.sent_at = timezone.now()
        notification.save()

        print(f"✅ Email notification sent to {notification.user.email}")

    except Exception as exc:
        print(f"❌ Email notification error: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

def _handle_failed_tokens(response, tokens, user):
    """Remove invalid FCM tokens"""
    from .models import FCMToken
    
    if response.failure_count > 0:
        failed_tokens = []
        for idx, resp in enumerate(response.responses):
            if not resp.success:
                failed_tokens.append(tokens[idx])
                logger.warning(f"FCM token failed: {resp.exception}")
        
        # Deactivate failed tokens
        FCMToken.objects.filter(
            user=user,
            token__in=failed_tokens
        ).update(is_active=False)

@shared_task
def process_scheduled_notifications():
    """
    This task runs every minute to check for due notifications
    """
    from .models import ScheduledNotification
    from apps.notification.services.notification_service import NotificationService
    
    # Get all notifications that are due
    due_notifications = ScheduledNotification.objects.filter(
        scheduled_at__lte=timezone.now(),
        status='pending'
    )
    
    logger.info(f"Found {due_notifications.count()} due notifications to process")
    
    for scheduled_notif in due_notifications:
        try:
            send_scheduled_notification.delay(scheduled_notif.id)
        except Exception as e:
            logger.error(f"Error queuing scheduled notification {scheduled_notif.id}: {e}")


@shared_task(bind=True, max_retries=3)
def send_scheduled_notification(self, scheduled_notification_id):
    """
    Send a scheduled notification to its target users
    """
    try:
        from .models import ScheduledNotification, Notification
        
        with transaction.atomic():
            scheduled_notif = ScheduledNotification.objects.select_for_update().get(
                id=scheduled_notification_id,
                status='pending'
            )
            
            # Mark as processing
            scheduled_notif.status = 'processing'
            scheduled_notif.save()
        
        # Get target users
        target_users = scheduled_notif.get_target_users()
        
        if not target_users.exists():
            scheduled_notif.status = 'failed'
            scheduled_notif.save()
            logger.warning(f"No target users found for scheduled notification {scheduled_notification_id}")
            return
        
        sent_count = 0
        failed_count = 0
        
        # Send to each user
        for user in target_users:
            try:
                # Check user preferences for each notification type
                preferences = getattr(user, 'notification_preference', None)
                
                for notif_type in scheduled_notif.notification_types:
                    if _should_send_to_user(user, notif_type, preferences):
                        # Create individual notification record
                        notification = Notification.objects.create(
                            user=user,
                            title=scheduled_notif.title,
                            message=scheduled_notif.message,
                            notification_type=notif_type,
                            data=scheduled_notif.data or {},
                            scheduled_notification=scheduled_notif
                        )
                        
                        # Dispatch based on type
                        if notif_type == 'push':
                            send_push_notification.delay(notification.id)
                        elif notif_type == 'in_app':
                            # In-app notifications are stored in DB and available via API; mark as sent
                            notification.sent_at = timezone.now()
                            notification.save()
                        elif notif_type == 'email':
                            send_email_notification.delay(notification.id)
                        
                        sent_count += 1
                        
            except Exception as e:
                logger.error(f"Error sending to user {user.id}: {e}")
                failed_count += 1
        
        # Update scheduled notification status
        scheduled_notif.sent_count = sent_count
        scheduled_notif.failed_count = failed_count
        scheduled_notif.sent_at = timezone.now()
        scheduled_notif.status = 'sent' if sent_count > 0 else 'failed'
        scheduled_notif.save()
        
        logger.info(f"Scheduled notification {scheduled_notification_id} sent to {sent_count} users, {failed_count} failures")
        
    except ScheduledNotification.DoesNotExist:
        logger.warning(f"Scheduled notification {scheduled_notification_id} not found or already processed")
    except Exception as exc:
        logger.error(f"Error processing scheduled notification {scheduled_notification_id}: {exc}")
        
        # Update status to failed and retry
        try:
            scheduled_notif = ScheduledNotification.objects.get(id=scheduled_notification_id)
            scheduled_notif.status = 'failed'
            scheduled_notif.save()
        except:
            pass
            
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def _should_send_to_user(user, notif_type, preferences):
    """Check if notification should be sent to user based on preferences"""
    if not preferences:
        return True
    
    preference_map = {
        'push': 'push_enabled',
        'email': 'email_enabled',
        'sms': 'sms_enabled',
        'in_app': 'in_app_enabled'  
    }
    
    return getattr(preferences, preference_map.get(notif_type, 'push_enabled'), True)