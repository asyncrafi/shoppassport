from apps.core.models import AppSettings
from rest_framework import serializers

class AppSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSettings
        fields = ['id', 'setting_type', 'content', 'last_updated']