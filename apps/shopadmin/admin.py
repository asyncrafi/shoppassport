from django.contrib import admin
from apps.shopadmin.models import Event

@admin.register(Event)
class Event(admin.ModelAdmin):
    list_display = ('shop_admin', 'name', 'created_at')
    search_fields = ('shop_admin__username', 'name')
    list_filter = ('created_at',)

