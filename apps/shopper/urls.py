from django.urls import path
from . import views

urlpatterns = [
    # Event Browsing
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/<int:event_id>/shops/', views.EventShopsView.as_view(), name='event-shops'),
    path('events/<int:event_id>/shops/<int:shop_id>/visits/', views.ShopVisitDetailsView.as_view(), name='shop-visit-details'),
    
    # Passport URLs
    path('my-passports/', views.MyPassportListView.as_view(), name='my-passports-list'),
    path('my-passports/<int:pk>/', views.MyPassportDetailView.as_view(), name='my-passport-detail'),
    path('passports/<str:passport_id>/', views.PassportByIdView.as_view(), name='passport-by-id'),
    path('passports/<int:passport_id>/download-qr/', views.DownloadQRCodeView.as_view(), name='download-qr-code'),
    
    # Check-in URLs
    path('check-ins/create/', views.CheckInCreateView.as_view(), name='check-in-create'),
    path('my-check-ins/', views.MyCheckInListView.as_view(), name='my-check-ins-list'),
    path('my-check-ins/<int:pk>/', views.MyCheckInDetailView.as_view(), name='my-check-in-detail'),
    path('my-check-ins/stats/', views.MyCheckInStatsView.as_view(), name='my-check-in-stats'),
    
    # Public Event Info
    path('events/<int:event_id>/passports/', views.PublicEventPassportsView.as_view(), name='event-passports'),
]
