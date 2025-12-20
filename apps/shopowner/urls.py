from django.urls import path
from . import views

urlpatterns = [
    # Participation Request URLs
    path('participation-requests/create/', views.ParticipantRequestCreateView.as_view(), name='participation-create'),
    path('my-participations/', views.MyParticipationListView.as_view(), name='my-participations-list'),
    path('my-participations/<int:pk>/', views.MyParticipationDetailView.as_view(), name='my-participation-detail'),
    path('my-participations/<int:pk>/cancel/', views.MyParticipationDeleteView.as_view(), name='my-participation-cancel'),
    
    # My Shop Events
    path('my-shop-events/', views.MyShopEventsView.as_view(), name='my-shop-events'),
]

