from django.urls import path
from . import views


urlpatterns = [
    # Shop CRUD URLs
    path('', views.ShopListView.as_view(), name='shop-list'),
    path('create/', views.ShopCreateView.as_view(), name='shop-create'),
    path('<int:pk>/', views.ShopDetailView.as_view(), name='shop-detail'),
    path('<int:pk>/update/', views.ShopUpdateView.as_view(), name='shop-update'),
    path('<int:pk>/delete/', views.ShopDeleteView.as_view(), name='shop-delete'),
    
    # Shop Events
    path('<int:shop_pk>/events/', views.ShopEventsListView.as_view(), name='shop-events-list'),
]