from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Notification, FCMToken, UserNotificationPreference
from .serializers import *
from .services.notification_service import NotificationService
import logging
from apps.core.utils.mixins import BaseResponseMixin

logger = logging.getLogger(__name__)

from rest_framework.response import Response

class NotificationViewSet(BaseResponseMixin, viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return self.success_response({'unread_count': count})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return self.success_response({'updated_count': updated})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return self.success_response({'notification_id': notification.id})

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        deleted_count = self.get_queryset().count()
        self.get_queryset().delete()
        return self.success_response({'deleted_count': deleted_count})



class FCMTokenViewSet(BaseResponseMixin, viewsets.ModelViewSet):
    serializer_class = FCMTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'create':
            return []  # No auth for registration
        return [IsAuthenticated()]
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return FCMToken.objects.filter(user=self.request.user)
        return FCMToken.objects.none()

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        token = serializer.validated_data['token']
        device_type = serializer.validated_data['device_type']

        if user:
            # Check if this exact token already exists
            existing_token = FCMToken.objects.filter(
                user=user,
                token=token,
                device_type=device_type
            ).first()

            if existing_token:
                # Just update it to active
                existing_token.is_active = True
                existing_token.save()
                return existing_token
            else:
                # Only deactivate old tokens if we're creating a genuinely new one
                FCMToken.objects.filter(
                    user=user,
                    device_type=device_type
                ).exclude(token=token).update(is_active=False)

        # Now the serializer can actually set is_active=True
        return serializer.save(user=user, is_active=True)

class SendNotificationView(BaseResponseMixin, APIView):
    """POST /api/notifications/send/ - Admin/System use"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SendNotificationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            for user_id in data['user_ids']:
                try:
                    NotificationService.send_notification(
                        user_id=user_id,
                        title=data['title'],
                        message=data['message'],
                        notification_types=data['notification_types'],
                        data=data.get('data', {})
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification to user {user_id}: {str(e)}")
                    continue
            
            return self.success_response(
                message=f'Notifications sent to {len(data["user_ids"])} users'
            )
        
        return self.error_response(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class NotificationPreferencesView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET /api/notifications/preferences/"""
        preferences, created = UserNotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preferences)
        return self.success_response(serializer.data)

    def put(self, request):
        """PUT /api/notifications/preferences/"""
        preferences, created = UserNotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preferences, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(serializer.data)
        return self.error_response(serializer.errors, status_code=400)
    

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from .models import ScheduledNotification
from apps.accounts.models import User

       
@api_view(['POST'])
def send_notification_to_all(request):
    """Send notification to all users or specific user"""
    title = request.data.get('title')
    message = request.data.get('message')
    recipient = request.data.get('recipient', 'all')  # 'all' or user_email

    if recipient == 'all':
        # Create notification for all users
        users = User.objects.filter(is_active=True)
        for user in users:
            Notification.objects.create(
                user=user,
                notification_type='push',
                title=title,
                message=message,
                sent_at=timezone.now()
            )
        return Response({'message': f'Notification sent to {users.count()} users'})
    else:
        # Send to specific user
        try:
            user = User.objects.get(email=recipient)
            Notification.objects.create(
                user=user,
                notification_type='push',
                title=title,
                message=message,
                sent_at=timezone.now()
            )
            return Response({'message': f'Notification sent to {user.email}'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


@api_view(['GET'])
def user_list_for_notifications(request):
    """Get simple user list for notification dropdown"""
    search = request.GET.get('search', '')
    
    users = User.objects.filter(is_active=True, is_blocked=False)
    
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(profile__name__icontains=search)
        )[:10]  # Limit to 10 results
    else:
        users = users[:20]  # Show first 20 users
    
    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'email': user.email,
            'name': user.profile.name if hasattr(user, 'profile') and user.profile.name else 'No Name',
            'display_name': f"{user.profile.name} ({user.email})" if hasattr(user, 'profile') and user.profile.name else user.email
        })
    
    return Response({
        'users': user_list,
        'total': User.objects.filter(is_active=True, is_blocked=False).count()
    })


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_notification(request, notification_id):
    """Delete a notification"""
    try:
        # Try to find in ScheduledNotification first
        try:
            notification = ScheduledNotification.objects.get(
                id=notification_id,
                created_by__is_staff=True
            )
            notification_title = notification.title
            notification.delete()
            return Response({
                'message': f'Scheduled notification "{notification_title}" has been deleted successfully'
            })
        except ScheduledNotification.DoesNotExist:
            pass

        # If not found, try Notification model
        try:
            notification = Notification.objects.get(
                id=notification_id,
                created_by__is_staff=True
            )
            notification_title = notification.title or 'Immediate Notification'
            notification.delete()
            return Response({
                'message': f'Immediate notification "{notification_title}" has been deleted successfully'
            })
        except Notification.DoesNotExist:
            pass

        return Response({'error': 'Notification not found'}, status=404)

    except Exception as e:
        return Response({
            'error': f'Error deleting notification: {str(e)}'
        }, status=500)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def bulk_delete_notifications(request):
    """Delete multiple notifications at once"""
    try:
        notification_ids = request.data.get('notification_ids', [])

        if not notification_ids:
            return Response({'error': 'No notification IDs provided'}, status=400)

        deleted_count = 0

        # Delete from ScheduledNotification
        scheduled_count = ScheduledNotification.objects.filter(
            id__in=notification_ids,
            created_by__is_staff=True
        ).count()
        ScheduledNotification.objects.filter(
            id__in=notification_ids,
            created_by__is_staff=True
        ).delete()
        deleted_count += scheduled_count

        # Delete from Notification
        immediate_count = Notification.objects.filter(
            id__in=notification_ids,
            created_by__is_staff=True
        ).count()
        Notification.objects.filter(
            id__in=notification_ids,
            created_by__is_staff=True
        ).delete()
        deleted_count += immediate_count

        return Response({
            'message': f'{deleted_count} notifications have been deleted successfully'
        })

    except Exception as e:
        return Response({
            'error': f'Error deleting notifications: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def schedule_notification(request):
    """
    Admin endpoint to schedule notifications
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['title', 'message', 'scheduled_at', 'notification_types', 'recipient_type']
        for field in required_fields:
            if not data.get(field):
                return Response({
                    'error': f'{field} is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse scheduled time
        try:
            scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00'))
        except ValueError:
            return Response({
                'error': 'Invalid datetime format. Use ISO format: 2024-12-25T10:30:00Z'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if scheduled time is in the future
        if scheduled_at <= timezone.now():
            return Response({
                'error': 'Scheduled time must be in the future'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create scheduled notification
        scheduled_notification = ScheduledNotification.objects.create(
            title=data['title'],
            message=data['message'],
            scheduled_at=scheduled_at,
            notification_types=data['notification_types'],
            recipient_type=data['recipient_type'],
            data=data.get('data', {}),
            created_by=request.user
        )
        
        # Add specific users if recipient_type is 'specific'
        if data['recipient_type'] == 'specific':
            user_ids = data.get('user_ids', [])
            if not user_ids:
                return Response({
                    'error': 'user_ids required when recipient_type is specific'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            users = User.objects.filter(id__in=user_ids, is_active=True)
            scheduled_notification.specific_users.set(users)
        
        return Response({
            'message': 'Notification scheduled successfully',
            'scheduled_notification': {
                'id': scheduled_notification.id,
                'title': scheduled_notification.title,
                'scheduled_at': scheduled_notification.scheduled_at,
                'recipient_type': scheduled_notification.recipient_type,
                'target_count': scheduled_notification.get_target_users().count(),
                'status': scheduled_notification.status
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Error scheduling notification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_immediate_notification(request):
    """
    Updated to save immediate notifications for tracking
    """
    try:
        data = request.data
        
        # Your existing validation...
        if not all([data.get('title'), data.get('message')]):
            return Response({
                'error': 'title and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        recipient_type = data.get('recipient_type', 'all')
        notification_types = data.get('notification_types', ['push'])
        
        # Get target users
        if recipient_type == 'all':
            target_users = User.objects.filter(is_active=True)
        else:
            user_ids = data.get('user_ids', [])
            if not user_ids:
                return Response({
                    'error': 'user_ids required when recipient_type is specific'
                }, status=status.HTTP_400_BAD_REQUEST)
            target_users = User.objects.filter(id__in=user_ids, is_active=True)
        
        if not target_users.exists():
            return Response({
                'error': 'No active users found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send notifications and save to Notification table for tracking
        sent_count = 0
        for user in target_users:
            try:
                # Send using your existing service
                from apps.notification.services.notification_service import NotificationService
                NotificationService.send_notification(
                    user_id=user.id,
                    title=data['title'],
                    message=data['message'],
                    notification_types=notification_types,
                    data=data.get('data', {})
                )
                
                # Save to Notification table for tracking
                for notif_type in notification_types:
                    Notification.objects.create(
                        user=user,
                        notification_type=notif_type,
                        title=data['title'],
                        message=data['message'],
                        data=data.get('data', {}),
                        sent_at=timezone.now(),
                        created_by=request.user
                    )
                
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending immediate notification to user {user.id}: {e}")
        
        return Response({
            'message': f'Notification sent to {sent_count} users',
            'sent_count': sent_count,
            'total_users': target_users.count()
        })
        
    except Exception as e:
        return Response({
            'error': f'Error sending notification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAdminUser])
def scheduled_notifications_list(request):
    """
    Get list of scheduled notifications for admin dashboard
    """
    scheduled_notifications = ScheduledNotification.objects.all()
    
    # Add filtering
    status_filter = request.GET.get('status')
    if status_filter:
        scheduled_notifications = scheduled_notifications.filter(status=status_filter)
    
    data = []
    for sn in scheduled_notifications:
        data.append({
            'id': sn.id,
            'title': sn.title,
            'message': sn.message[:100] + '...' if len(sn.message) > 100 else sn.message,
            'scheduled_at': sn.scheduled_at,
            'status': sn.status,
            'recipient_type': sn.recipient_type,
            'target_count': sn.get_target_users().count(),
            'sent_count': sn.sent_count,
            'failed_count': sn.failed_count,
            'notification_types': sn.notification_types,
            'created_at': sn.created_at,
            'created_by': sn.created_by.email if sn.created_by else None
        })
    
    return Response({
        'scheduled_notifications': data,
        'total': len(data)
    })


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def cancel_scheduled_notification(request, notification_id):
    """
    Cancel a scheduled notification (only if status is pending)
    """
    try:
        scheduled_notif = ScheduledNotification.objects.get(id=notification_id)
        
        if scheduled_notif.status != 'pending':
            return Response({
                'error': f'Cannot cancel notification with status: {scheduled_notif.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        scheduled_notif.status = 'cancelled'
        scheduled_notif.save()
        
        return Response({
            'message': f'Scheduled notification "{scheduled_notif.title}" has been cancelled'
        })
        
    except ScheduledNotification.DoesNotExist:
        return Response({
            'error': 'Scheduled notification not found'
        }, status=status.HTTP_404_NOT_FOUND)



# views.py - Add this new unified view

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
from itertools import chain
from operator import attrgetter

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_notifications_unified(request):
    """
    Unified API to get all notifications created by admin users (is_staff=True)
    Combines ScheduledNotification and Notification data with filtering
    """
    try:
        # Get query parameters
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        notification_type_filter = request.GET.get('notification_type', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        created_by_filter = request.GET.get('created_by', '')
        
        # Base querysets - only admin created notifications
        scheduled_qs = ScheduledNotification.objects.filter(
            created_by__is_staff=True
        ).select_related('created_by')
        
        # For immediate notifications - filter by admin users who sent them
        immediate_qs = Notification.objects.filter(
            created_by__is_staff=True
        ).select_related('created_by')
        
        # Apply search filter
        if search:
            scheduled_qs = scheduled_qs.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )
            immediate_qs = immediate_qs.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )
        
        # Apply status filter
        if status_filter:
            scheduled_qs = scheduled_qs.filter(status=status_filter)
            # For immediate notifications, map status
            if status_filter == 'sent':
                immediate_qs = immediate_qs.filter(sent_at__isnull=False)
            elif status_filter == 'pending':
                immediate_qs = immediate_qs.none()  # Immediate are never pending
        
        # Apply notification type filter
        if notification_type_filter:
            scheduled_qs = scheduled_qs.filter(
                notification_types__contains=[notification_type_filter]
            )
            immediate_qs = immediate_qs.filter(
                notification_type=notification_type_filter
            )
        
        # Apply date filters
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                scheduled_qs = scheduled_qs.filter(created_at__gte=date_from_dt)
                immediate_qs = immediate_qs.filter(created_at__gte=date_from_dt)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                scheduled_qs = scheduled_qs.filter(created_at__lte=date_to_dt)
                immediate_qs = immediate_qs.filter(created_at__lte=date_to_dt)
            except ValueError:
                pass
        
        # Apply created_by filter
        if created_by_filter:
            try:
                created_by_id = int(created_by_filter)
                scheduled_qs = scheduled_qs.filter(created_by_id=created_by_id)
                # For immediate notifications, you'll need to adjust based on your model
                # immediate_qs = immediate_qs.filter(created_by_id=created_by_id)
            except ValueError:
                pass
        
        # Convert to unified format
        notifications = []
        
        # Process scheduled notifications
        for sn in scheduled_qs:
            notifications.append({
                'id': f"scheduled_{sn.id}",
                'original_id': sn.id,
                'type': 'scheduled',
                'title': sn.title,
                'message': sn.message,
                'notification_types': sn.notification_types,
                'status': sn.status,
                'recipient_type': sn.recipient_type,
                'target_count': sn.get_target_users().count() if hasattr(sn, 'get_target_users') else 0,
                'sent_count': sn.sent_count,
                'failed_count': sn.failed_count,
                'scheduled_at': sn.scheduled_at,
                'sent_at': sn.sent_at,
                'created_at': sn.created_at,
                'created_by': {
                    'id': sn.created_by.id,
                    'email': sn.created_by.email,
                    'name': f"{sn.created_by.first_name} {sn.created_by.last_name}".strip()
                },
                'is_due': sn.scheduled_at <= timezone.now() and sn.status == 'pending' if sn.scheduled_at else False,
                'data': getattr(sn, 'data', {}),
            })
        
        # Process immediate notifications
        for notif in immediate_qs:
            notifications.append({
                'id': f"immediate_{notif.id}",
                'original_id': notif.id,
                'type': 'immediate',
                'title': notif.title or 'Immediate Notification',
                'message': notif.message or '',
                'notification_types': [notif.notification_type] if notif.notification_type else ['push'],
                'status': 'sent' if notif.sent_at else 'pending',
                'recipient_type': 'specific',  # Immediate are usually to specific users
                'target_count': 1,
                'sent_count': 1 if notif.sent_at else 0,
                'failed_count': 0 if notif.sent_at else 1,
                'scheduled_at': None,
                'sent_at': notif.sent_at,
                'created_at': notif.created_at,
                'created_by': {
                    'id': None,  # You might need to add a field to track this
                    'email': 'admin@system.com',  # Placeholder
                    'name': 'System Admin'
                },
                'recipient': {
                    'id': notif.user.id if notif.user else None,
                    'email': notif.user.email if notif.user else None
                },
                'is_due': False,
                'data': notif.data or {},
            })
        
        # Sort by created_at (most recent first)
        notifications.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        start = (page - 1) * per_page
        end = start + per_page
        
        total_count = len(notifications)
        paginated_notifications = notifications[start:end]
        
        # Calculate stats
        stats = {
            'total': total_count,
            'scheduled': len([n for n in notifications if n['type'] == 'scheduled']),
            'immediate': len([n for n in notifications if n['type'] == 'immediate']),
            'by_status': {
                'pending': len([n for n in notifications if n['status'] == 'pending']),
                'sent': len([n for n in notifications if n['status'] == 'sent']),
                'failed': len([n for n in notifications if n['status'] == 'failed']),
                'cancelled': len([n for n in notifications if n['status'] == 'cancelled']),
            },
            'due_scheduled': len([n for n in notifications if n.get('is_due', False)]),
        }
        
        return Response({
            'notifications': paginated_notifications,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total': total_count,
                'total_pages': (total_count + per_page - 1) // per_page,
                'has_next': end < total_count,
                'has_prev': page > 1
            },
            'stats': stats,
            'filters_applied': {
                'search': search,
                'status': status_filter,
                'notification_type': notification_type_filter,
                'date_from': date_from,
                'date_to': date_to,
                'created_by': created_by_filter
            }
        })
    
    except Exception as e:
        return Response({
            'error': f'Error fetching notifications: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_notifications_stats(request):
    """
    Get comprehensive stats for admin dashboard
    """
    try:
        # Stats from ScheduledNotification (admin created)
        scheduled_stats = ScheduledNotification.objects.filter(
            created_by__is_staff=True
        ).aggregate(
            total_scheduled=Count('id'),
            pending_scheduled=Count('id', filter=Q(status='pending')),
            sent_scheduled=Count('id', filter=Q(status='sent')),
            failed_scheduled=Count('id', filter=Q(status='failed')),
            cancelled_scheduled=Count('id', filter=Q(status='cancelled')),
        )
        
        # Due notifications
        now = timezone.now()
        due_count = ScheduledNotification.objects.filter(
            created_by__is_staff=True,
            scheduled_at__lte=now,
            status='pending'
        ).count()
        
        # Stats from immediate notifications
        immediate_stats = Notification.objects.filter(
            # Add your admin filter here
        ).aggregate(
            total_immediate=Count('id'),
            sent_immediate=Count('id', filter=Q(sent_at__isnull=False)),
        )
        
        # Notification type breakdown for scheduled
        push_count = ScheduledNotification.objects.filter(
            created_by__is_staff=True,
            notification_types__contains=['push']
        ).count()
        
        email_count = ScheduledNotification.objects.filter(
            created_by__is_staff=True,
            notification_types__contains=['email']
        ).count()
        
        in_app_count = ScheduledNotification.objects.filter(
            created_by__is_staff=True,
            notification_types__contains=['in_app']
        ).count()
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        last_week = now - timedelta(days=7)
        
        recent_scheduled = ScheduledNotification.objects.filter(
            created_by__is_staff=True,
            created_at__gte=last_week
        ).count()
        
        recent_immediate = Notification.objects.filter(
            created_at__gte=last_week
        ).count()
        
        return Response({
            'total_notifications': scheduled_stats['total_scheduled'] + immediate_stats['total_immediate'],
            'scheduled': {
                'total': scheduled_stats['total_scheduled'],
                'pending': scheduled_stats['pending_scheduled'],
                'sent': scheduled_stats['sent_scheduled'],
                'failed': scheduled_stats['failed_scheduled'],
                'cancelled': scheduled_stats['cancelled_scheduled'],
                'due': due_count,
            },
            'immediate': {
                'total': immediate_stats['total_immediate'],
                'sent': immediate_stats['sent_immediate'],
            },
            'by_notification_type': {
                'push': push_count,
                'email': email_count,
                'in_app': in_app_count,
            },
            'recent_activity': {
                'scheduled_last_week': recent_scheduled,
                'immediate_last_week': recent_immediate,
            },
            'overall_status': {
                'pending': scheduled_stats['pending_scheduled'],
                'sent': scheduled_stats['sent_scheduled'] + immediate_stats['sent_immediate'],
                'failed': scheduled_stats['failed_scheduled'],
                'cancelled': scheduled_stats['cancelled_scheduled'],
            }
        })
    
    except Exception as e:
        return Response({
            'error': f'Error fetching stats: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_creators_list(request):
    """
    Get list of admin users who have created notifications
    """
    try:
        # Get admins who created scheduled notifications
        admin_users = User.objects.filter(
            is_staff=True,
            created_schedules__isnull=False
        ).distinct().values(
            'id', 'email', 'first_name', 'last_name'
        ).annotate(
            notification_count=Count('created_schedules')
        )
        
        creators = []
        for user in admin_users:
            creators.append({
                'id': user['id'],
                'email': user['email'],
                'name': f"{user['first_name']} {user['last_name']}".strip() or user['email'],
                'notification_count': user['notification_count']
            })
        
        return Response({
            'creators': creators,
            'total': len(creators)
        })
    
    except Exception as e:
        return Response({
            'error': f'Error fetching creators: {str(e)}'
        }, status=500)

