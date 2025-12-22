from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Event, EventImage, EventShop, 
    EventShopParticipant, EventPassport, ShopperCheckIn
)

# Inline Admin Classes
class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1
    readonly_fields = ['uploaded_at']
    fields = ['image', 'uploaded_at', 'event']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


class EventShopInline(admin.TabularInline):
    model = EventShop
    extra = 1
    readonly_fields = ['created_at']


class EventPassportInline(admin.TabularInline):
    model = EventPassport
    extra = 1
    readonly_fields = ['created_at', 'shop_qr_code_preview']
    fields = ['passport_id', 'shop', 'valid_from', 'valid_to', 'shop_qr_code', 'shop_qr_code_preview']
    
    def shop_qr_code_preview(self, obj):
        if obj.shop_qr_code:
            return format_html('<img src="{}" width="100" height="100" />', obj.shop_qr_code.url)
        return "No QR Code"
    shop_qr_code_preview.short_description = 'QR Preview'


# Main Admin Classes
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop_admin', 'location', 'from_date', 'to_date', 'created_at', 'event_images_count']
    list_filter = ['from_date', 'to_date', 'created_at']
    search_fields = ['name', 'location', 'shop_admin__email', 'shop_admin__name']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    inlines = [EventImageInline, EventShopInline, EventPassportInline]
    fieldsets = [
        ('Basic Information', {
            'fields': ['shop_admin', 'name', 'about_the_event', 'location']
        }),
        ('Coordinates', {
            'fields': ['latitude', 'longitude'],
            'classes': ['collapse']
        }),
        ('Date & Time', {
            'fields': ['from_date', 'to_date']
        }),
        ('Contact Information', {
            'fields': ['contact_person_name'],
            'classes': ['collapse']
        }),
        ('Media', {
            'fields': ['image', 'image_preview']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" height="150" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Main Image Preview'
    
    def event_images_count(self, obj):
        return obj.images.count()
    event_images_count.short_description = 'Additional Images'


@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ['event', 'uploaded_at', 'image_preview']
    list_filter = ['uploaded_at', 'event']
    search_fields = ['event__name']
    readonly_fields = ['uploaded_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(EventShop)
class EventShopAdmin(admin.ModelAdmin):
    list_display = ['event', 'shop', 'created_at']
    list_filter = ['created_at', 'event']
    search_fields = ['event__name', 'shop__shop_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EventShopParticipant)
class EventShopParticipantAdmin(admin.ModelAdmin):
    list_display = ['shopper', 'participant_name', 'event_shop', 'participant_email', 'participant_phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['participant_name', 'participant_email', 'event_shop__event__name', 'event_shop__shop__shop_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Participant Information', {
            'fields': ['event_shop', 'shopper', 'participant_name', 'participant_email', 'participant_phone', 'contact_number']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(EventPassport)
class EventPassportAdmin(admin.ModelAdmin):
    list_display = ['passport_id', 'event', 'shop', 'valid_from', 'valid_to', 'created_at', 'qr_code_preview']
    list_filter = ['valid_from', 'valid_to', 'created_at']
    search_fields = ['passport_id', 'event__name', 'shop__shop_name']
    readonly_fields = ['created_at', 'updated_at', 'qr_code_preview']
    
    fieldsets = [
        ('Passport Information', {
            'fields': ['event', 'shop', 'passport_id', 'description']
        }),
        ('Validity Period', {
            'fields': ['valid_from', 'valid_to']
        }),
        ('QR Code', {
            'fields': ['shop_qr_code', 'qr_code_preview']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def qr_code_preview(self, obj):
        if obj.shop_qr_code:
            return format_html('<img src="{}" width="150" height="150" />', obj.shop_qr_code.url)
        return "No QR Code"
    qr_code_preview.short_description = 'QR Code Preview'


@admin.register(ShopperCheckIn)
class ShopperCheckInAdmin(admin.ModelAdmin):
    list_display = ['event_passport', 'shopper', 'check_in_time', 'created_at']
    list_filter = ['check_in_time', 'created_at']
    search_fields = ['event_passport__passport_id', 'shopper__email', 'shopper__name']
    readonly_fields = ['check_in_time', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('event_passport', 'shopper')