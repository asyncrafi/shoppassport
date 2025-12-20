
"""
Shop Admin Serializers
File: apps/shopadmin/serializers.py
"""

from rest_framework import serializers
from apps.shopadmin.models import Event, EventShop, EventShopParticipant, EventPassport, ShopperCheckIn
from apps.shop.models import Shop


# ==================== EVENT SERIALIZERS ====================

class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for event listings"""
    admin_name = serializers.CharField(source='shop_admin.get_full_name', read_only=True)
    total_shops = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'location', 'from_date', 'to_date',
            'image', 'admin_name', 'total_shops', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_total_shops(self, obj):
        return obj.event_shops.count()
    
    def get_status(self, obj):
        from datetime import date
        today = date.today()
        if obj.from_date and obj.to_date:
            if today < obj.from_date:
                return 'upcoming'
            elif today > obj.to_date:
                return 'completed'
            else:
                return 'ongoing'
        return 'draft'


class EventDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single event view"""
    admin_name = serializers.CharField(source='shop_admin.get_full_name', read_only=True)
    admin_email = serializers.EmailField(source='shop_admin.email', read_only=True)
    total_shops = serializers.SerializerMethodField()
    total_passports = serializers.SerializerMethodField()
    total_check_ins = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'shop_admin', 'name', 'about_the_event', 'location',
            'latitude', 'longitude', 'from_date', 'to_date',
            'contact_person_name', 'image', 'admin_name', 'admin_email',
            'total_shops', 'total_passports', 'total_check_ins',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_shops(self, obj):
        return obj.event_shops.count()
    
    def get_total_passports(self, obj):
        return obj.passports.count()
    
    def get_total_check_ins(self, obj):
        return ShopperCheckIn.objects.filter(event_passport__event=obj).count()


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating events"""
    
    class Meta:
        model = Event
        fields = [
            'shop_admin', 'name', 'about_the_event', 'location',
            'latitude', 'longitude', 'from_date', 'to_date',
            'contact_person_name', 'image'
        ]
    
    def validate(self, data):
        if data.get('from_date') and data.get('to_date'):
            if data['from_date'] > data['to_date']:
                raise serializers.ValidationError({
                    'to_date': 'End date must be after start date'
                })
        return data
