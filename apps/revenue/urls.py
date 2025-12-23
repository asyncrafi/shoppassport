from django.urls import path
from .views import (
    # Event Admin APIs
    EventEntryFeeView,
    VerifyAdminPaymentView,
    MyPaymentsView,
    CheckEventPaymentView,
    
    # Super Admin Dashboard APIs
    EarningsOverviewView,
    AllPaymentsView,
    MonthlySummaryView,
    RevenueStatsView,
    TopEventAdminsView,
)

urlpatterns = [
    # ===== Event Admin APIs =====
    path('entry-fee/', EventEntryFeeView.as_view(), name='entry-fee'),
    path('verify-payment/', VerifyAdminPaymentView.as_view(), name='verify-payment'),
    path('my-payments/', MyPaymentsView.as_view(), name='my-payments'),
    path('check-payment/<int:event_id>/', CheckEventPaymentView.as_view(), name='check-payment'),
    
    # ===== Super Admin Dashboard APIs =====
    path('admin/earnings-overview/', EarningsOverviewView.as_view(), name='earnings-overview'),
    path('admin/all-payments/', AllPaymentsView.as_view(), name='all-payments'),
    path('admin/monthly-summary/', MonthlySummaryView.as_view(), name='monthly-summary'),
    path('admin/revenue-stats/', RevenueStatsView.as_view(), name='revenue-stats'),
    path('admin/top-admins/', TopEventAdminsView.as_view(), name='top-admins'),
]