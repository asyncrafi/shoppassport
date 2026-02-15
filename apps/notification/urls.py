from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'list', views.NotificationViewSet, basename='notifications')
router.register(r'fcm-tokens', views.FCMTokenViewSet, basename='fcm-tokens')

urlpatterns = [
    path('', include(router.urls)),
    
    # Existing endpoints
    path('send/', views.SendNotificationView.as_view(), name='send-notification'),
    path('preferences/', views.NotificationPreferencesView.as_view(), name='notification-preferences'),
    path('users/', views.user_list_for_notifications, name='user-list-notifications'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete-notification'),
    path('bulk-delete/', views.bulk_delete_notifications, name='bulk-delete-notifications'),

    # admin existing endpoints...
    path('admin/send-immediate/', views.send_immediate_notification, name='admin-send-immediate'),
    path('admin/schedule/', views.schedule_notification, name='admin-schedule-notification'),
    path('admin/scheduled/<int:notification_id>/cancel/', views.cancel_scheduled_notification, name='admin-cancel-scheduled'),

    path('admin-notifications/unified/', views.admin_notifications_unified, name='admin-notifications-unified'),
    path('admin-notifications/stats/', views.admin_notifications_stats, name='admin-notifications-stats'),
    path('admin-notifications/creators/', views.admin_creators_list, name='admin-creators-list'),
    
]
