# admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import EventEntryFee, EventAdminPayment, EarningsSummary
from django.utils import timezone
from datetime import datetime
import calendar


# Inline classes
class EventAdminPaymentInline(admin.TabularInline):
    model = EventAdminPayment
    extra = 0
    can_delete = False
    readonly_fields = ('revenuecat_transaction_id', 'amount_paid', 'status', 'payment_date')
    fields = ('revenuecat_transaction_id', 'amount_paid', 'status', 'payment_date')
    max_num = 1  # Only one payment per event


# Custom filters
class ActiveEntryFeeFilter(admin.SimpleListFilter):
    title = 'Active Status'
    parameter_name = 'is_active'
    
    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'inactive':
            return queryset.filter(is_active=False)


class PaymentStatusFilter(admin.SimpleListFilter):
    title = 'Payment Status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return [
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())


class PlatformFilter(admin.SimpleListFilter):
    title = 'Platform'
    parameter_name = 'platform'
    
    def lookups(self, request, model_admin):
        return [
            ('android', 'Android'),
            ('ios', 'iOS'),
            ('web', 'Web'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(platform=self.value())


# Custom admin classes
@admin.register(EventEntryFee)
class EventEntryFeeAdmin(admin.ModelAdmin):
    list_display = ('fee_name', 'amount_with_currency', 'is_active', 'product_ids_summary', 'created_at')
    list_filter = (ActiveEntryFeeFilter,)
    search_fields = ('fee_name', 'description', 'revenuecat_product_id_android', 'revenuecat_product_id_ios')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('fee_name', 'amount', 'currency', 'is_active', 'description')
        }),
        ('RevenueCat Product IDs', {
            'fields': ('revenuecat_product_id_android', 'revenuecat_product_id_ios', 'revenuecat_product_id_web'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def amount_with_currency(self, obj):
        return f"{obj.currency} {obj.amount}"
    amount_with_currency.short_description = 'Amount'
    
    def product_ids_summary(self, obj):
        platforms = []
        if obj.revenuecat_product_id_android:
            platforms.append('Android')
        if obj.revenuecat_product_id_ios:
            platforms.append('iOS')
        if obj.revenuecat_product_id_web:
            platforms.append('Web')
        return ', '.join(platforms) if platforms else 'No IDs'
    product_ids_summary.short_description = 'Available Platforms'
    
    actions = ['activate_fees', 'deactivate_fees']
    
    def activate_fees(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} fee(s) activated.")
    activate_fees.short_description = "Activate selected fees"
    
    def deactivate_fees(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} fee(s) deactivated.")
    deactivate_fees.short_description = "Deactivate selected fees"


@admin.register(EventAdminPayment)
class EventAdminPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment_id', 
        'event_admin', 
        'event_name',
        'amount_display',
        'platform_icon',
        'status_badge',
        'payment_date_formatted',
        'verified_status'
    )
    list_filter = (PaymentStatusFilter, PlatformFilter, 'payment_year', 'payment_month')
    search_fields = (
        'event__name',
        'event_admin__username',
        'event_admin__email',
        'revenuecat_transaction_id',
        'store_transaction_id'
    )
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'payment_month', 
        'payment_year',
        'payment_date',
        'revenuecat_transaction_id',
        'revenuecat_user_id',
        'revenuecat_product_id'
    )
    list_select_related = ('event', 'event_admin', 'entry_fee')
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'event', 
                'event_admin', 
                'entry_fee',
                'revenuecat_transaction_id',
                'store_transaction_id'
            )
        }),
        ('Payment Information', {
            'fields': (
                'amount_paid', 
                'currency', 
                'platform', 
                'status',
                'payment_date',
                ('verified_at', 'refunded_at')
            )
        }),
        ('RevenueCat Details', {
            'fields': (
                'revenuecat_user_id',
                'revenuecat_product_id'
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'payment_month', 'payment_year'),
            'classes': ('collapse',),
        }),
    )
    
    def payment_id(self, obj):
        # Display short transaction ID
        if len(obj.revenuecat_transaction_id) > 15:
            return f"{obj.revenuecat_transaction_id[:15]}..."
        return obj.revenuecat_transaction_id
    payment_id.short_description = 'Transaction ID'
    
    def event_name(self, obj):
        return obj.event.name
    event_name.short_description = 'Event'
    
    def amount_display(self, obj):
        return f"{obj.currency} {obj.amount_paid}"
    amount_display.short_description = 'Amount'
    
    def platform_icon(self, obj):
        icons = {
            'android': '📱',
            'ios': '🍎',
            'web': '🌐'
        }
        return format_html(
            '<span style="font-size: 16px;" title="{}">{}</span>',
            obj.get_platform_display(),
            icons.get(obj.platform, '❓')
        )
    platform_icon.short_description = 'Platform'
    
    def status_badge(self, obj):
        colors = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
            'refunded': 'gray'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'
    
    def payment_date_formatted(self, obj):
        return obj.payment_date.strftime('%Y-%m-%d %H:%M')
    payment_date_formatted.short_description = 'Date'
    
    def verified_status(self, obj):
        if obj.verified_at:
            return format_html(
                '<span style="color: green;">✓ Verified</span><br><small>{}</small>',
                obj.verified_at.strftime('%Y-%m-%d')
            )
        return format_html('<span style="color: orange;">Pending</span>')
    verified_status.short_description = 'Verification'
    
    actions = ['mark_as_completed', 'mark_as_refunded', 'generate_receipts']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='completed',
            verified_at=timezone.now()
        )
        self.message_user(request, f"{updated} payment(s) marked as completed.")
    mark_as_completed.short_description = "Mark selected payments as completed"
    
    def mark_as_refunded(self, request, queryset):
        updated = queryset.filter(status='completed').update(
            status='refunded',
            refunded_at=timezone.now()
        )
        self.message_user(request, f"{updated} payment(s) marked as refunded.")
    mark_as_refunded.short_description = "Mark selected payments as refunded"
    
    def generate_receipts(self, request, queryset):
        # Placeholder for receipt generation action
        self.message_user(request, f"Receipt generation would be triggered for {queryset.count()} payment(s).")
    generate_receipts.short_description = "Generate receipts for selected payments"


@admin.register(EarningsSummary)
class EarningsSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'period',
        'total_revenue_display',
        'total_transactions',
        'platform_breakdown',
        'updated_display'
    )
    list_filter = ('year', 'month')
    search_fields = ('year',)
    readonly_fields = ('created_at', 'updated_at', 'all_fields_display')
    actions = ['refresh_summaries']
    
    fieldsets = (
        ('Summary Information', {
            'fields': ('year', 'month', 'currency')
        }),
        ('Revenue Summary', {
            'fields': ('total_revenue', 'total_transactions')
        }),
        ('Platform Breakdown', {
            'fields': ('android_revenue', 'ios_revenue', 'web_revenue'),
            'classes': ('collapse',),
        }),
        ('Complete Data', {
            'fields': ('all_fields_display',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def period(self, obj):
        month_name = calendar.month_name[obj.month]
        return f"{month_name} {obj.year}"
    period.short_description = 'Period'
    
    def total_revenue_display(self, obj):
        return f"{obj.currency} {obj.total_revenue:,.2f}"
    total_revenue_display.short_description = 'Total Revenue'
    
    def platform_breakdown(self, obj):
        return format_html(
            '<small>Android: {}<br>iOS: {}<br>Web: {}</small>',
            f"{obj.currency} {obj.android_revenue:,.2f}",
            f"{obj.currency} {obj.ios_revenue:,.2f}",
            f"{obj.currency} {obj.web_revenue:,.2f}"
        )
    platform_breakdown.short_description = 'Platform Breakdown'
    
    def updated_display(self, obj):
        return obj.updated_at.strftime('%Y-%m-%d %H:%M')
    updated_display.short_description = 'Last Updated'
    
    def all_fields_display(self, obj):
        """Display all fields in a readable format"""
        return format_html("""
            <div style="padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                <strong>Year:</strong> {}<br>
                <strong>Month:</strong> {} ({})<br>
                <strong>Total Revenue:</strong> {} {}<br>
                <strong>Total Transactions:</strong> {}<br>
                <strong>Android Revenue:</strong> {} {}<br>
                <strong>iOS Revenue:</strong> {} {}<br>
                <strong>Web Revenue:</strong> {} {}<br>
                <strong>Created:</strong> {}<br>
                <strong>Updated:</strong> {}
            </div>
        """,
            obj.year,
            obj.month, calendar.month_name[obj.month],
            obj.currency, obj.total_revenue,
            obj.total_transactions,
            obj.currency, obj.android_revenue,
            obj.currency, obj.ios_revenue,
            obj.currency, obj.web_revenue,
            obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        )
    all_fields_display.short_description = 'Complete Summary'
    
    def refresh_summaries(self, request, queryset):
        for summary in queryset:
            EarningsSummary.update_summary(summary.year, summary.month)
        self.message_user(request, f"{queryset.count()} summary(s) refreshed.")
    refresh_summaries.short_description = "Refresh selected summaries"

