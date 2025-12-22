from django.contrib import admin
from django.utils.html import format_html
from .models import Shop, ShopCoverImage

# Inline Admin for ShopCoverImage
class ShopCoverImageInline(admin.TabularInline):
    model = ShopCoverImage
    extra = 1
    readonly_fields = ['uploaded_at', 'image_preview']
    fields = ['image', 'uploaded_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />', 
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'

# Custom Filter for Shop Owner
class ShopOwnerFilter(admin.SimpleListFilter):
    title = 'shop owner'
    parameter_name = 'shop_owner'

    def lookups(self, request, model_admin):
        # Get unique shop owners who have shops
        from apps.accounts.models import User
        owners = User.objects.filter(shops__isnull=False).distinct()
        return [(owner.id, f"{owner.email} ({owner.name if hasattr(owner, 'name') else 'No name'})") for owner in owners]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(shop_owner_id=self.value())
        return queryset

# Main Admin for Shop
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = [
        'shop_name', 
        'shop_owner_display', 
        'email', 
        'shop_location', 
        'contact_person_name',
        'cover_images_count',
        'logo_preview',
        'created_at'
    ]
    list_filter = [ShopOwnerFilter, 'created_at', 'updated_at']
    search_fields = [
        'shop_name', 
        'email', 
        'shop_owner__email', 
        'shop_owner__username',
        'shop_owner__first_name',
        'shop_owner__last_name',
        'contact_person_name',
        'shop_location'
    ]
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'logo_preview', 
        'cover_image_preview',
        'pdf_pattern_download'
    ]
    inlines = [ShopCoverImageInline]
    
    fieldsets = [
        ('Basic Information', {
            'fields': [
                'shop_owner', 
                'shop_name', 
                'email', 
                'shop_location'
            ]
        }),
        ('Description', {
            'fields': ['about_the_shop'],
            'classes': ['wide']
        }),
        ('Contact Information', {
            'fields': [
                'contact_person_name', 
                'contact_person_phone'
            ]
        }),
        ('Media', {
            'fields': [
                'shop_logo', 
                'logo_preview',
                'cover_image', 
                'cover_image_preview'
            ]
        }),
        ('Files', {
            'fields': [
                'upload_pdf_pattern',
                'pdf_pattern_download'
            ],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    # Custom methods for display and previews
    def shop_owner_display(self, obj):
        if obj.shop_owner:
            return f"{obj.shop_owner.email}"
        return "No Owner"
    shop_owner_display.short_description = 'Owner'
    
    def logo_preview(self, obj):
        if obj.shop_logo:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />', 
                obj.shop_logo.url
            )
        return "No Logo"
    logo_preview.short_description = 'Logo'
    
    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" width="150" height="75" style="object-fit: cover;" />', 
                obj.cover_image.url
            )
        return "No Cover Image"
    cover_image_preview.short_description = 'Main Cover Preview'
    
    def pdf_pattern_download(self, obj):
        if obj.upload_pdf_pattern:
            return format_html(
                '<a href="{}" target="_blank" class="button">Download PDF</a>',
                obj.upload_pdf_pattern.url
            )
        return "No PDF Uploaded"
    pdf_pattern_download.short_description = 'PDF Pattern'
    
    def cover_images_count(self, obj):
        return obj.cover_images.count()
    cover_images_count.short_description = 'Additional Covers'
    
    # Custom actions
    actions = ['export_shop_info', 'clear_pdf_patterns']
    
    def export_shop_info(self, request, queryset):
        # Placeholder for export functionality
        # Could be implemented to export to CSV/Excel
        self.message_user(
            request, 
            f"Preparing export for {queryset.count()} shop(s)."
        )
    export_shop_info.short_description = "Export selected shops"
    
    def clear_pdf_patterns(self, request, queryset):
        updated = queryset.update(upload_pdf_pattern=None)
        self.message_user(
            request, 
            f"Cleared PDF patterns for {updated} shop(s)."
        )
    clear_pdf_patterns.short_description = "Clear PDF patterns"
    
    # Performance optimization
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('shop_owner').prefetch_related('cover_images')
    
    # Ordering and pagination
    ordering = ['-created_at']
    list_per_page = 25
    
    # Date hierarchy for quick navigation
    date_hierarchy = 'created_at'

# Admin for ShopCoverImage
@admin.register(ShopCoverImage)
class ShopCoverImageAdmin(admin.ModelAdmin):
    list_display = ['shop', 'uploaded_at', 'image_preview']
    list_filter = ['uploaded_at', 'shop']
    search_fields = ['shop__shop_name', 'shop__email']
    readonly_fields = ['uploaded_at', 'image_preview']
    
    fieldsets = [
        ('Image Information', {
            'fields': ['shop', 'image', 'image_preview']
        }),
        ('Timestamp', {
            'fields': ['uploaded_at'],
            'classes': ['collapse']
        }),
    ]
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="100" style="object-fit: cover;" />', 
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'
    
    # Performance optimization
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('shop')
    
    # Ordering
    ordering = ['-uploaded_at']
    list_per_page = 20