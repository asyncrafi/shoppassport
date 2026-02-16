from celery import shared_task
from firebase_admin import messaging
from django.utils import timezone
from apps.accounts.models import User
import logging
import firebase_admin
from firebase_admin import credentials
from celery.schedules import crontab
from django.db import transaction
import os
import traceback


logger = logging.getLogger(__name__)

# Initialize Firebase with APNs configuration
from django.conf import settings

def initialize_firebase():
    """Safely initialize Firebase with detailed logging"""
    logger.info("🔥 Attempting to initialize Firebase...")
    
    if firebase_admin._apps:
        logger.info("✅ Firebase already initialized")
        return True
    
    try:
        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        logger.info(f"🔍 Firebase credentials path: {cred_path}")
        
        # Check if path is absolute or relative
        if not os.path.isabs(cred_path):
            # Try both relative to BASE_DIR and current directory
            base_dir_path = os.path.join(settings.BASE_DIR, cred_path)
            logger.info(f"🔍 Trying BASE_DIR path: {base_dir_path}")
            
            if os.path.exists(base_dir_path):
                cred_path = base_dir_path
                logger.info(f"✅ Found credentials at BASE_DIR path")
            else:
                logger.warning(f"⚠️ Credentials not found at BASE_DIR path")
        
        # Check if file exists
        if not os.path.exists(cred_path):
            logger.error(f"❌ Firebase credentials file NOT FOUND: {cred_path}")
            logger.error(f"❌ Current working directory: {os.getcwd()}")
            logger.error(f"❌ Files in current directory: {os.listdir('.')}")
            if os.path.exists('/app'):
                logger.error(f"❌ Files in /app: {os.listdir('/app')}")
            return False
        
        logger.info(f"✅ Firebase credentials file found at: {cred_path}")
        
        # Try to read and validate JSON
        try:
            import json
            with open(cred_path, 'r') as f:
                cred_data = json.load(f)
                logger.info(f"✅ Credentials JSON loaded successfully")
                logger.info(f"🔍 Project ID: {cred_data.get('project_id', 'NOT FOUND')}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in credentials file: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error reading credentials file: {e}")
            return False
            
        # Initialize Firebase
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase Admin SDK initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {e}")
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        return False

# Try to initialize on module load
firebase_initialized = initialize_firebase()


@shared_task(bind=True, max_retries=3)
def send_push_notification(self, notification_id):
    logger.info(f"🚀 Starting send_push_notification task for notification_id: {notification_id}")
    
    try:
        from .models import Notification, FCMToken
        
        # Check Firebase initialization
        if not firebase_admin._apps:
            logger.error("❌ Firebase not initialized, attempting to initialize...")
            if not initialize_firebase():
                logger.error("❌ Firebase initialization failed, cannot send push notification")
                # Mark notification as attempted but failed
                try:
                    notification = Notification.objects.get(id=notification_id)
                    notification.sent_at = timezone.now()
                    notification.save()
                    logger.warning(f"⚠️ Marked notification {notification_id} as sent (but Firebase unavailable)")
                except Exception as save_err:
                    logger.error(f"❌ Error saving notification: {save_err}")
                return

        logger.info(f"✅ Firebase is initialized, proceeding...")

        # Get notification
        try:
            notification = Notification.objects.get(id=notification_id)
            logger.info(f"✅ Notification found: {notification.title}")
        except Notification.DoesNotExist:
            logger.error(f"❌ Notification {notification_id} does not exist")
            return
        
        # Get FCM tokens
        tokens = FCMToken.objects.filter(
            user=notification.user,
            is_active=True
        ).values_list('token', flat=True)

        logger.info(f"🔍 User {notification.user.id} ({notification.user.email}) has {len(tokens)} active tokens")

        if not tokens:
            logger.warning(f"⚠️ No active FCM tokens for user {notification.user.id}")
            notification.sent_at = timezone.now()
            notification.save()
            return

        # Print tokens for debugging (first 50 chars only)
        for idx, token in enumerate(tokens):
            logger.info(f"🔑 Token {idx + 1}: {token[:50]}...")

        # Build message
        try:
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
            logger.info(f"✅ Message object created successfully")
        except Exception as msg_err:
            logger.error(f"❌ Error creating message: {msg_err}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise

        # Send message
        try:
            logger.info(f"📤 Sending message with APNs config to {len(tokens)} tokens...")
            response = messaging.send_each_for_multicast(message)
            logger.info(f"✅ Firebase response - Success: {response.success_count}, Failures: {response.failure_count}")
        except Exception as send_err:
            logger.error(f"❌ Error sending message: {send_err}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise

        # Log individual failures
        if response.failure_count > 0:
            logger.warning(f"⚠️ {response.failure_count} tokens failed")
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    logger.error(f"❌ Token {idx} failed: {resp.exception}")

        # Handle failed tokens
        _handle_failed_tokens(response, tokens, notification.user)

        # Mark as sent
        notification.sent_at = timezone.now()
        notification.save()

        logger.info(f"✅ COMPLETE - Push notification {notification_id} sent to {len(tokens)} tokens, {response.failure_count} failures")

    except Exception as exc:
        logger.error(f"❌ Push notification error for {notification_id}: {exc}")
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        
        # Retry with exponential backoff
        retry_delay = 60 * (2 ** self.request.retries)
        logger.warning(f"🔄 Retrying in {retry_delay} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
        raise self.retry(exc=exc, countdown=retry_delay)
    

@shared_task(bind=True, max_retries=3)
def send_email_notification(self, notification_id):
    logger.info(f"📧 Starting send_email_notification task for notification_id: {notification_id}")
    
    try:
        from apps.core.utils.mailgun_service import MailgunEmailService
        from .models import Notification
        from django.utils import timezone

        notification = Notification.objects.get(id=notification_id)
        logger.info(f"✅ Notification found: {notification.title}")
        
        mailgun_service = MailgunEmailService()
        logger.info(f"📧 Sending email to {notification.user.email}")

        # Extract attachment info from notification data
        attachment = None
        if notification.data and 'pdf_file_path' in notification.data:
            attachment = notification.data.get('pdf_file_path')
            logger.info(f"📎 Attaching PDF file: {attachment}")

        # Build nice HTML email content
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">{notification.title}</h2>
                    <p style="font-size: 16px; margin-bottom: 15px;">{notification.message}</p>
                    <hr style="border: none; border-top: 1px solid #ecf0f1;">
                    <p style="font-size: 12px; color: #7f8c8d;">
                        This is an automatic notification from ShopHopApp.<br>
                        Please find your shop details attached.
                    </p>
                </div>
            </body>
        </html>
        """

        mailgun_service.send_transactional_email(
            to_email=notification.user.email,
            to_name=notification.user.profile.name,
            subject=notification.title,
            html_content=html_content,
            text_content=notification.message,
            attachment=attachment
        )

        notification.sent_at = timezone.now()
        notification.save()

        logger.info(f"✅ Email notification sent to {notification.user.email}")

    except Exception as exc:
        logger.error(f"❌ Email notification error: {exc}")
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def _handle_failed_tokens(response, tokens, user):
    """Remove invalid FCM tokens"""
    from .models import FCMToken
    
    if response.failure_count > 0:
        failed_tokens = []
        for idx, resp in enumerate(response.responses):
            if not resp.success:
                failed_tokens.append(tokens[idx])
                logger.warning(f"⚠️ FCM token failed: {resp.exception}")
        
        # Deactivate failed tokens
        deactivated = FCMToken.objects.filter(
            user=user,
            token__in=failed_tokens
        ).update(is_active=False)
        
        logger.info(f"🗑️ Deactivated {deactivated} invalid tokens for user {user.id}")


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
    
    logger.info(f"📅 Found {due_notifications.count()} due notifications to process")
    
    for scheduled_notif in due_notifications:
        try:
            logger.info(f"📋 Queuing scheduled notification {scheduled_notif.id}")
            send_scheduled_notification.delay(scheduled_notif.id)
        except Exception as e:
            logger.error(f"❌ Error queuing scheduled notification {scheduled_notif.id}: {e}")


@shared_task(bind=True, max_retries=3)
def send_scheduled_notification(self, scheduled_notification_id):
    """
    Send a scheduled notification to its target users
    """
    logger.info(f"📤 Processing scheduled notification {scheduled_notification_id}")
    
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
            logger.info(f"✅ Marked notification {scheduled_notification_id} as processing")
        
        # Get target users
        target_users = scheduled_notif.get_target_users()
        logger.info(f"👥 Found {target_users.count()} target users")
        
        if not target_users.exists():
            scheduled_notif.status = 'failed'
            scheduled_notif.save()
            logger.warning(f"⚠️ No target users found for scheduled notification {scheduled_notification_id}")
            return
        
        sent_count = 0
        failed_count = 0
        
        # Send to each user
        for user in target_users:
            try:
                # Check user preferences for each notification type
                preferences = getattr(user, 'notification_preference', None)
                logger.info(f"👤 Processing user {user.id} ({user.email})")
                
                for notif_type in scheduled_notif.notification_types:
                    if _should_send_to_user(user, notif_type, preferences):
                        logger.info(f"  📨 Sending {notif_type} notification to user {user.id}")
                        
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
                    else:
                        logger.info(f"  ⏭️ Skipping {notif_type} notification for user {user.id} (disabled in preferences)")
                        
            except Exception as e:
                logger.error(f"❌ Error sending to user {user.id}: {e}")
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                failed_count += 1
        
        # Update scheduled notification status
        scheduled_notif.sent_count = sent_count
        scheduled_notif.failed_count = failed_count
        scheduled_notif.sent_at = timezone.now()
        scheduled_notif.status = 'sent' if sent_count > 0 else 'failed'
        scheduled_notif.save()
        
        logger.info(f"✅ Scheduled notification {scheduled_notification_id} complete - Sent: {sent_count}, Failed: {failed_count}")
        
    except ScheduledNotification.DoesNotExist:
        logger.warning(f"⚠️ Scheduled notification {scheduled_notification_id} not found or already processed")
    except Exception as exc:
        logger.error(f"❌ Error processing scheduled notification {scheduled_notification_id}: {exc}")
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        
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
        logger.debug(f"  ℹ️ No preferences found for user {user.id}, allowing all notifications")
        return True
    
    preference_map = {
        'push': 'push_enabled',
        'email': 'email_enabled',
        'sms': 'sms_enabled',
        'in_app': 'in_app_enabled'  
    }
    
    pref_field = preference_map.get(notif_type, 'push_enabled')
    is_enabled = getattr(preferences, pref_field, True)
    
    logger.debug(f"  ℹ️ User {user.id} preference for {notif_type}: {is_enabled}")
    return is_enabled