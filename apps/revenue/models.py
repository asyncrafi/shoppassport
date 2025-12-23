# models.py - ADD THESE MODELS

from django.db import models
from apps.accounts.models import User
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from django.conf import settings
from apps.shopadmin.models import Event


class EventEntryFee(models.Model):
    """Super admin configures the entry fee for event admins"""
    fee_name = models.CharField(max_length=100, default="Event Creation Fee")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # RevenueCat product IDs
    revenuecat_product_id_android = models.CharField(max_length=100, blank=True, null=True)
    revenuecat_product_id_ios = models.CharField(max_length=100, blank=True, null=True)
    revenuecat_product_id_web = models.CharField(max_length=100, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.fee_name} - ${self.amount}"
    
    class Meta:
        verbose_name = "Event Entry Fee"
        verbose_name_plural = "Event Entry Fees"


class EventAdminPayment(models.Model):
    """Track when event admins pay the entry fee"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]
    
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='admin_payment')
    event_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_payments')
    entry_fee = models.ForeignKey(EventEntryFee, on_delete=models.SET_NULL, null=True, blank=True)
    
    # RevenueCat transaction details
    revenuecat_transaction_id = models.CharField(max_length=255, unique=True)
    revenuecat_user_id = models.CharField(max_length=255)
    revenuecat_product_id = models.CharField(max_length=100)
    
    # Payment details
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    store_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    
    # For tracking
    payment_month = models.IntegerField(blank=True, null=True)  # 1-12
    payment_year = models.IntegerField(blank=True, null=True)   # 2024, 2025
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
    # Save first to let Django set payment_date
        if not self.pk:  # Only on creation
            super().save(*args, **kwargs)
            # Now payment_date is set, update month/year
            if not self.payment_month:
                self.payment_month = self.payment_date.month
            if not self.payment_year:
                self.payment_year = self.payment_date.year
            # Save again with month/year
            super().save(update_fields=['payment_month', 'payment_year'])
        else:
            # On update, just save normally
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.event_admin.username} - {self.event.name} - ${self.amount_paid}"
    
    class Meta:
        verbose_name = "Event Admin Payment"
        verbose_name_plural = "Event Admin Payments"
        ordering = ['-payment_date']


class EarningsSummary(models.Model):
    """Monthly earnings summary - generated automatically"""
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    currency = models.CharField(max_length=3, default='USD')
    
    # Platform breakdown
    android_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ios_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    web_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['year', 'month']
        ordering = ['-year', '-month']
        verbose_name = "Earnings Summary"
        verbose_name_plural = "Earnings Summaries"
    
    def __str__(self):
        return f"{self.year}-{self.month:02d} - ${self.total_revenue}"
    
    @classmethod
    def update_summary(cls, year, month):
        """Update summary for a specific month"""
        payments = EventAdminPayment.objects.filter(
            payment_year=year,
            payment_month=month,
            status='completed'
        )
        
        total_revenue = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        total_transactions = payments.count()
        
        android_revenue = payments.filter(platform='android').aggregate(
            Sum('amount_paid'))['amount_paid__sum'] or 0
        ios_revenue = payments.filter(platform='ios').aggregate(
            Sum('amount_paid'))['amount_paid__sum'] or 0
        web_revenue = payments.filter(platform='web').aggregate(
            Sum('amount_paid'))['amount_paid__sum'] or 0
        
        summary, created = cls.objects.update_or_create(
            year=year,
            month=month,
            defaults={
                'total_revenue': total_revenue,
                'total_transactions': total_transactions,
                'android_revenue': android_revenue,
                'ios_revenue': ios_revenue,
                'web_revenue': web_revenue,
            }
        )
        return summary