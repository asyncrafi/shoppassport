from rest_framework import serializers
from apps.shopadmin.models import Event, EventShop, EventShopParticipant, EventPassport, ShopperCheckIn
from apps.shop.models import Shop, ShopCoverImage
from apps.accounts.models import User

class ShopCoverImageSerializer(serializers.ModelSerializer):
    """Serializer for Shop Cover Images"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    image = serializers.ImageField()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

    class Meta:
        model = ShopCoverImage
        fields = ['id', 'shop_name', 'shop', 'image', 'uploaded_at']
        read_only_fields = ['id', 'shop', 'uploaded_at']


class ShopListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for shop listings"""
    owner_name = serializers.CharField(source='shop_owner.get_full_name', read_only=True)
    cover_images = ShopCoverImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Shop
        fields = [
            'id', 'shop_name', 'email', 'shop_location', 
            'shop_logo', 'owner_name', 'cover_images', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ShopDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single shop view"""
    owner_name = serializers.CharField(source='shop_owner.get_full_name', read_only=True)
    owner_email = serializers.EmailField(source='shop_owner.email', read_only=True)
    total_events = serializers.SerializerMethodField()
    cover_images = ShopCoverImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Shop
        fields = [
            'id', 'shop_owner', 'shop_name', 'email', 'shop_location',
            'shop_logo', 'cover_images', 'status', 'about_the_shop', 'contact_person_name',
            'contact_person_phone', 'upload_pdf_pattern',
            'owner_name', 'owner_email', 'total_events',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_events(self, obj):
        return obj.event_shops.count()


class ShopCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating shops with multiple cover images"""
    cover_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Shop
        fields = [
            'shop_owner', 'shop_name', 'email', 'shop_location',
            'shop_logo', 'about_the_shop', 'contact_person_name',
            'contact_person_phone', 'upload_pdf_pattern', 'cover_images', 'status'
        ]
    
    def validate_email(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value
    
    def create(self, validated_data):
        cover_images_data = validated_data.pop('cover_images', [])
        shop = Shop.objects.create(**validated_data)
        
        # Create multiple cover images
        for image_data in cover_images_data:
            ShopCoverImage.objects.create(shop=shop, image=image_data)
        
        return shop
    
    def update(self, instance, validated_data):
        cover_images_data = validated_data.pop('cover_images', None)
        
        # Update shop fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle cover images if provided
        if cover_images_data is not None:
            # Option 1: Add new images (keep existing ones)
            for image_data in cover_images_data:
                ShopCoverImage.objects.create(shop=instance, image=image_data)
            
        return instance


# ==================== EVENT SHOP SERIALIZERS ====================

class EventShopListSerializer(serializers.ModelSerializer):
    """List of shops in an event"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    shop_location = serializers.CharField(source='shop.shop_location', read_only=True)
    shop_logo = serializers.ImageField(source='shop.shop_logo', read_only=True)
    total_participants = serializers.SerializerMethodField()

    cover_images = ShopCoverImageSerializer(source='shop.cover_images', many=True, read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.shop.shop_logo and request:
            representation['shop_logo'] = request.build_absolute_uri(instance.shop.shop_logo.url)
        return representation
        
    class Meta:
        model = EventShop
        fields = [
            'id', 'event', 'shop', 'event_name', 'shop_name',
            'shop_location', 'shop_logo', 'cover_images', 'total_participants', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']
    
    def get_total_participants(self, obj):
        return obj.participants.count()


class EventShopCreateSerializer(serializers.ModelSerializer):
    """Add shop to event"""
    
    class Meta:
        model = EventShop
        fields = ['event', 'shop']
    
    def validate(self, data):
        # Check if shop already added to event
        if EventShop.objects.filter(event=data['event'], shop=data['shop']).exists():
            raise serializers.ValidationError('Shop already added to this event')
        return data