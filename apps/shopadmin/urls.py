from django.urls import path
from . import views

urlpatterns = [
    # Event URLs
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/create/', views.EventCreateView.as_view(), name='event-create'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('events/<int:pk>/update/', views.EventUpdateView.as_view(), name='event-update'),
    path('events/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event-delete'),
    
    # Event Shops URLs
    path('events/<int:event_pk>/shops/', views.EventShopsListView.as_view(), name='event-shops-list'),
    path('event-shops/create/', views.EventShopCreateView.as_view(), name='event-shop-create'),
    path('event-shops/<int:pk>/delete/', views.EventShopDeleteView.as_view(), name='event-shop-delete'),
    
    # Participant URLs
    path('participants/', views.ParticipantListView.as_view(), name='participant-list'),
    path('participants/<int:pk>/', views.ParticipantDetailView.as_view(), name='participant-detail'),
    path('participants/<int:pk>/accept/', views.ParticipantAcceptView.as_view(), name='participant-accept'),
    path('participants/<int:pk>/reject/', views.ParticipantRejectView.as_view(), name='participant-reject'),
    path('participants/<int:pk>/delete/', views.ParticipantDeleteView.as_view(), name='participant-delete'),
    
    # Passport URLs
    path('passports/', views.PassportListView.as_view(), name='passport-list'),
    path('passports/create/', views.PassportCreateView.as_view(), name='passport-create'),
    path('passports/<int:pk>/', views.PassportDetailView.as_view(), name='passport-detail'),
    path('passports/<int:pk>/update/', views.PassportUpdateView.as_view(), name='passport-update'),
    path('passports/<int:pk>/delete/', views.PassportDeleteView.as_view(), name='passport-delete'),
]
