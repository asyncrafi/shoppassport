# serializers.py

from rest_framework import serializers
from .models import EventEntryFee, EventAdminPayment, EarningsSummary
from apps.accounts.models import User
from apps.shopadmin.models import Event
from django.db.models import Sum, Count


class EventEntryFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventEntryFee
        fields = '__all__'


class EventAdminPaymentSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source='event.name', read_only=True)
    admin_name = serializers.CharField(source='event_admin.username', read_only=True)
    admin_email = serializers.CharField(source='event_admin.email', read_only=True)
    
    class Meta:
        model = EventAdminPayment
        fields = '__all__'
        read_only_fields = ['payment_date', 'verified_at', 'created_at', 'payment_month', 'payment_year']


class VerifyAdminPaymentSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    revenuecat_transaction_id = serializers.CharField(max_length=255)
    revenuecat_user_id = serializers.CharField(max_length=255)
    revenuecat_product_id = serializers.CharField(max_length=100)
    platform = serializers.ChoiceField(choices=['android', 'ios', 'web'])
    store_transaction_id = serializers.CharField(required=False, allow_blank=True)


class EarningsSummarySerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EarningsSummary
        fields = '__all__'
    
    def get_month_name(self, obj):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return months[obj.month - 1] if 1 <= obj.month <= 12 else ''


class EarningsOverviewSerializer(serializers.Serializer):
    """Main earnings overview data"""
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_transactions = serializers.IntegerField()
    year_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    month_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    
    # Growth
    revenue_growth_percentage = serializers.FloatField()
    
    # Platform breakdown
    platform_breakdown = serializers.DictField()
    
    # Monthly data for chart
    monthly_earnings = serializers.ListField()