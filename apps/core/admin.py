from django.contrib import admin
from .models import AppSettings, CommonData


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ('setting_type', 'get_setting_display', 'last_updated', 'content_preview')
    list_filter = ('setting_type', 'last_updated')
    search_fields = ('setting_type', 'content')
    ordering = ('setting_type',)

    fieldsets = (
        ('Setting Information', {
            'fields': ('setting_type', 'content')
        }),
        ('Metadata', {
            'fields': ('last_updated',),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('last_updated',)

    def get_setting_display(self, obj):
        return obj.__str__()

    get_setting_display.short_description = 'Setting Name'

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content

    content_preview.short_description = 'Content Preview'

    def has_add_permission(self, request):
        # Limit to only 3 instances (one for each setting type)
        if AppSettings.objects.count() >= 3:
            return False
        return super().has_add_permission(request)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # Adding new object
            # Show only unused setting types
            used_types = AppSettings.objects.values_list('setting_type', flat=True)
            available_choices = [
                choice for choice in AppSettings.SETTING_TYPES
                if choice[0] not in used_types
            ]
            form.base_fields['setting_type'].choices = available_choices
        return form

admin.site.register(CommonData)


admin.site.site_header = "Hop Across America Admin Panel"
admin.site.site_title = "Hop Across America Portal"
admin.site.index_title = "Welcome to Hop Across America"