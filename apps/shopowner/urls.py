from django.urls import path
from . import views

urlpatterns = [

    # Event Shops URLs
    path('events/<int:event_pk>/shops/', views.EventShopsListView.as_view(), name='event-shops-list'),
    path('event-shops/create/', views.EventShopCreateView.as_view(), name='event-shop-create'),
    path('events/<int:event_pk>/shop-requests/', views.ShopRequestListView.as_view(), name='shop-requests-list'),
    path('shop-requests/<int:pk>/approve/', views.ShopRequestApproveView.as_view(), name='shop-request-approve'),
    path('shop-requests/<int:pk>/reject/', views.ShopRequestRejectView.as_view(), name='shop-request-reject'),
    path('event-shops/<int:pk>/delete/', views.EventShopDeleteView.as_view(), name='event-shop-delete'),
    
    # Shop-level Participation Request URLs (OLD - keep for backward compatibility)
    path('participation-requests/create/', views.ParticipantRequestCreateView.as_view(), name='participation-create'),
    path('my-participations/', views.MyParticipationListView.as_view(), name='my-participations-list'),
    path('my-participations/<int:pk>/', views.MyParticipationDetailView.as_view(), name='my-participation-detail'),
    path('my-participations/<int:pk>/cancel/', views.MyParticipationDeleteView.as_view(), name='my-participation-cancel'),
    
    # Event-level Participation Request URLs (NEW)
    path('event-participation-requests/create/', views.EventParticipationRequestCreateView.as_view(), name='event-participation-create'),
    path('my-event-participations/', views.MyEventParticipationListView.as_view(), name='my-event-participations-list'),
    path('my-event-participations/<int:pk>/', views.MyEventParticipationDetailView.as_view(), name='my-event-participation-detail'),
    path('my-event-participations/<int:pk>/cancel/', views.MyEventParticipationDeleteView.as_view(), name='my-event-participation-cancel'),
    
    path('event-participations/<int:pk>/approve/', views.EventParticipationApproveView.as_view(), name='event-participation-approve'),
    path('event-participations/<int:pk>/reject/', views.EventParticipationRejectView.as_view(), name='event-participation-reject'),

    path('events/<int:event_id>/participations/', views.EventParticipationListView.as_view(), name='event-participations-list'),
    
    # My Shop Events
    path('my-shop-events/', views.MyShopEventsView.as_view(), name='my-shop-events'),
    path('my-shops/', views.MyShopsListView.as_view(), name='my-shops-list'),
]

