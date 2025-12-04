from django.contrib import admin
from apps.shopadmin.models import CreateEvent

@admin.register(CreateEvent)
class CreateEvent(admin.ModelAdmin):
    list_display = ('user', 'shop', 'created_at')
    search_fields = ('user__username', 'shop__name')
    list_filter = ('created_at',)

