from django.urls import path
from . import views

app_name = 'shopper'

urlpatterns = [
    # Passport URLs
    path('my-passports/', views.MyPassportListView.as_view(), name='my-passports-list'),
    path('my-passports/<int:pk>/', views.MyPassportDetailView.as_view(), name='my-passport-detail'),
    path('passports/<str:passport_id>/', views.PassportByIdView.as_view(), name='passport-by-id'),
    
    # Check-in URLs
    path('check-ins/create/', views.CheckInCreateView.as_view(), name='check-in-create'),
    path('my-check-ins/', views.MyCheckInListView.as_view(), name='my-check-ins-list'),
    path('my-check-ins/<int:pk>/', views.MyCheckInDetailView.as_view(), name='my-check-in-detail'),
    path('my-check-ins/stats/', views.MyCheckInStatsView.as_view(), name='my-check-in-stats'),
    
    # Public Event Info
    path('events/<int:event_id>/passports/', views.PublicEventPassportsView.as_view(), name='event-passports'),
]
