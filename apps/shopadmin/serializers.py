from rest_framework import serializers
from apps.shopadmin.models import Event, EventImage,  EventShop, EventShopParticipant, EventPassport, ShopperCheckIn
from apps.shop.models import Shop
from apps.shop.serializers import ShopListSerializer


class EventImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()
    
    class Meta:
        model = EventImage
        fields = ['id', 'image', 'uploaded_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.image and request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation


class EventListSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='shop_admin.get_full_name', read_only=True)
    total_shops = serializers.SerializerMethodField()
    event_date_status = serializers.SerializerMethodField()

    images = EventImageSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'location', 'from_date', 'to_date',
            'images', 'admin_name', 'total_shops', 'status', 'event_date_status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_total_shops(self, obj):
        return obj.event_shops.count()

    def get_event_date_status(self, obj):
        from datetime import date
        today = date.today()
        if obj.from_date and obj.to_date:
            if today < obj.from_date:
                return 'upcoming'
            elif today > obj.to_date:
                return 'Ended'
            else:
                return 'ongoing'
        return 'draft'


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Event
        fields = [
            'shop_admin', 'name', 'about_the_event', 'location',
            'latitude', 'longitude', 'from_date', 'to_date',
            'contact_person_name', 'images', 'status'
        ]

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        event = Event.objects.create(**validated_data)
        
        # Create multiple images
        for image_data in images_data:
            EventImage.objects.create(event=event, image=image_data)
        
        return event

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        
        # Update event fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle images if provided
        if images_data is not None:
            # Option: Replace all existing images
            instance.images.all().delete()
            for image_data in images_data:
                EventImage.objects.create(event=instance, image=image_data)
        
        return instance

    def validate(self, data):
        if data.get('from_date') and data.get('to_date'):
            if data['from_date'] > data['to_date']:
                raise serializers.ValidationError({
                    'to_date': 'End date must be after start date'
                })
        return data
    
class EventDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single event view"""
    admin_name = serializers.CharField(source='shop_admin.get_full_name', read_only=True)
    admin_email = serializers.EmailField(source='shop_admin.email', read_only=True)
    total_shops = serializers.SerializerMethodField()
    total_passports = serializers.SerializerMethodField()
    total_check_ins = serializers.SerializerMethodField()
    participating_shops = ShopListSerializer(source='event_shops__shop', many=True, read_only=True)

    images = EventImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'shop_admin', 'name', 'about_the_event', 'location',
            'latitude', 'longitude', 'from_date', 'to_date',
            'contact_person_name', 'images', 'admin_name', 'admin_email',
            'total_shops', 'total_passports', 'total_check_ins',
            'participating_shops', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_shops(self, obj):
        return obj.event_shops.count()
    
    def get_total_passports(self, obj):
        return obj.passports.count()
    
    def get_total_check_ins(self, obj):
        return ShopperCheckIn.objects.filter(event_passport__event=obj).count()
    
    

class ParticipantListSerializer(serializers.ModelSerializer):
    """List participants with basic info"""
    event_name = serializers.CharField(source='event_shop.event.name', read_only=True)
    shop_name = serializers.CharField(source='event_shop.shop.shop_name', read_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = EventShopParticipant
        fields = [
            'id', 'event_shop', 'participant_name', 'participant_email',
            'participant_phone', 'contact_number', 'event_name', 'shop_name',
            'accepted', 'rejected', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_status(self, obj):
        if obj.accepted:
            return 'accepted'
        elif obj.rejected:
            return 'rejected'
        else:
            return 'pending'


class ParticipantCreateSerializer(serializers.ModelSerializer):
    """Shop owner creates participation request"""
    
    class Meta:
        model = EventShopParticipant
        fields = [
            'event_shop', 'participant_name', 'participant_email',
            'participant_phone', 'contact_number'
        ]
    
    def validate_participant_email(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value


class ParticipantUpdateSerializer(serializers.ModelSerializer):
    """Update participant status"""
    
    class Meta:
        model = EventShopParticipant
        fields = ['accepted', 'rejected']
    
    def validate(self, data):
        if data.get('accepted') and data.get('rejected'):
            raise serializers.ValidationError('Cannot accept and reject simultaneously')
        return data



class PassportListSerializer(serializers.ModelSerializer):
    """List passports"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    total_check_ins = serializers.SerializerMethodField()
    
    class Meta:
        model = EventPassport
        fields = [
            'id', 'event', 'shop', 'passport_id', 'shop_qr_code',
            'event_name', 'shop_name', 'valid_from', 'valid_to',
            'total_check_ins', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_total_check_ins(self, obj):
        return obj.check_ins.count()


class PassportDetailSerializer(serializers.ModelSerializer):
    """Detailed passport view"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_location = serializers.CharField(source='event.location', read_only=True)
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    shop_location = serializers.CharField(source='shop.shop_location', read_only=True)
    shop_logo = serializers.ImageField(source='shop.shop_logo', read_only=True)
    total_check_ins = serializers.SerializerMethodField()
    
    class Meta:
        model = EventPassport
        fields = [
            'id', 'event', 'shop', 'passport_id', 'shop_qr_code',
            'description', 'valid_from', 'valid_to', 'event_name',
            'event_location', 'shop_name', 'shop_location', 'shop_logo',
            'total_check_ins', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_check_ins(self, obj):
        return obj.check_ins.count()


class PassportCreateSerializer(serializers.ModelSerializer):
    """Create passport"""
    
    class Meta:
        model = EventPassport
        fields = [
            'event', 'shop', 'passport_id', 'shop_qr_code',
            'description', 'valid_from', 'valid_to'
        ]
    
    def validate_passport_id(self, value):
        if EventPassport.objects.filter(passport_id=value).exists():
            raise serializers.ValidationError('Passport ID already exists')
        return value
    
    def validate(self, data):
        if data.get('valid_from') and data.get('valid_to'):
            if data['valid_from'] > data['valid_to']:
                raise serializers.ValidationError({
                    'valid_to': 'End date must be after start date'
                })
        return data



class CheckInListSerializer(serializers.ModelSerializer):
    """List check-ins"""
    shopper_name = serializers.CharField(source='shopper.get_full_name', read_only=True)
    shopper_email = serializers.EmailField(source='shopper.email', read_only=True)
    event_name = serializers.CharField(source='event_passport.event.name', read_only=True)
    shop_name = serializers.CharField(source='event_passport.shop.shop_name', read_only=True)
    passport_id = serializers.CharField(source='event_passport.passport_id', read_only=True)
    
    class Meta:
        model = ShopperCheckIn
        fields = [
            'id', 'event_passport', 'shopper', 'shopper_name',
            'shopper_email', 'event_name', 'shop_name', 'passport_id',
            'check_in_time', 'created_at'
        ]
        read_only_fields = ['id', 'check_in_time', 'created_at']


class CheckInDetailSerializer(serializers.ModelSerializer):
    """Detailed check-in view"""
    shopper_name = serializers.CharField(source='shopper.get_full_name', read_only=True)
    shopper_email = serializers.EmailField(source='shopper.email', read_only=True)
    event_passport_details = PassportDetailSerializer(source='event_passport', read_only=True)
    
    class Meta:
        model = ShopperCheckIn
        fields = [
            'id', 'event_passport', 'shopper', 'shopper_name',
            'shopper_email', 'event_passport_details',
            'check_in_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'check_in_time', 'created_at', 'updated_at']


class CheckInCreateSerializer(serializers.ModelSerializer):
    """Create check-in (shopper scans QR)"""
    
    class Meta:
        model = ShopperCheckIn
        fields = ['event_passport', 'shopper']
    
    def validate(self, data):
        # Check if shopper already checked in to this passport
        if ShopperCheckIn.objects.filter(
            event_passport=data['event_passport'],
            shopper=data['shopper']
        ).exists():
            raise serializers.ValidationError('Already checked in to this location')
        
        # Check if passport is valid
        from datetime import date
        passport = data['event_passport']
        today = date.today()
        
        if passport.valid_from and today < passport.valid_from:
            raise serializers.ValidationError('Passport not yet valid')
        
        if passport.valid_to and today > passport.valid_to:
            raise serializers.ValidationError('Passport has expired')
        
        return data