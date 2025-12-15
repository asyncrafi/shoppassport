from rest_framework import serializers
from apps.shopadmin.models import Event, EventShop, EventShopParticipant, EventPassport, ShopperCheckIn
from apps.shop.models import Shop
from apps.accounts.models import User

class ShopListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for shop listings"""
    owner_name = serializers.CharField(source='shop_owner.get_full_name', read_only=True)
    
    class Meta:
        model = Shop
        fields = [
            'id', 'shop_name', 'email', 'shop_location', 
            'shop_logo', 'owner_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ShopDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single shop view"""
    owner_name = serializers.CharField(source='shop_owner.get_full_name', read_only=True)
    owner_email = serializers.EmailField(source='shop_owner.email', read_only=True)
    total_events = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = [
            'id', 'shop_owner', 'shop_name', 'email', 'shop_location',
            'shop_logo', 'about_the_shop', 'contact_person_name',
            'contact_person_phone', 'cover_image', 'upload_pdf_pattern',
            'owner_name', 'owner_email', 'total_events',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_events(self, obj):
        return obj.event_shops.count()


class ShopCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating shops"""
    
    class Meta:
        model = Shop
        fields = [
            'shop_owner', 'shop_name', 'email', 'shop_location',
            'shop_logo', 'about_the_shop', 'contact_person_name',
            'contact_person_phone', 'cover_image', 'upload_pdf_pattern'
        ]
    
    def validate_email(self, value):
        if value and not '@' in value:
            raise serializers.ValidationError("Invalid email format")
        return value
