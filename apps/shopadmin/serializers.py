from rest_framework import serializers
from apps.shopadmin.models import Event, EventImage, EventParticipant,  EventShop, EventShopParticipant, EventPassport, ShopperCheckIn
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
    admin_name = serializers.CharField(source='shop_admin.profile.name', read_only=True)
    admin_email = serializers.EmailField(source='shop_admin.email', read_only=True)
    admin_phone = serializers.CharField(source='shop_admin.profile.phone', read_only=True)
    total_shops = serializers.SerializerMethodField()
    event_date_status = serializers.SerializerMethodField()

    images = EventImageSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'about_the_event', 'location', 'latitude', 'longitude', 'from_date', 'to_date',
            'images', 'admin_name', 'admin_email', 'admin_phone', 'total_shops', 'status', 'event_date_status', 'created_at'
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
    shopper_avatar = serializers.ImageField(source='shopper.profile.profile_picture', read_only=True)
    
    def get_shopper_avatar(self, obj):
        """Get shopper avatar with null checks"""
        request = self.context.get('request')
        
        # Check if shopper exists
        if not obj.shopper:
            return None
        
        # Check if profile exists
        if not hasattr(obj.shopper, 'profile'):
            return None
        
        # Check if profile_picture exists
        if not obj.shopper.profile.profile_picture:
            return None
        
        # Build absolute URI
        if request:
            return request.build_absolute_uri(obj.shopper.profile.profile_picture.url)
        
        return obj.shopper.profile.profile_picture.url

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation
    
    
    class Meta:
        model = EventShopParticipant
        fields = [
            'id', 'event_shop', 'shopper', 'participant_name', 'participant_email',
            'participant_phone', 'contact_number', 'event_name', 'shop_name',
            'status', 'created_at', 'shopper_avatar'
        ]
        read_only_fields = ['id', 'created_at', 'status']


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
    
    def create(self, validated_data):
        # Get the user from context (passed from the view)
        user = self.context.get('request').user
        validated_data['shopper'] = user
        # Ensure request starts as pending
        validated_data.setdefault('status', 'pending')
        return super().create(validated_data)
    

class ParticipantUpdateSerializer(serializers.ModelSerializer):
    """Update participant status"""
    
    class Meta:
        model = EventShopParticipant
        fields = ['shopper', 'participant_name', 'participant_email', 'participant_phone', 'contact_number']


class EventParticipantListSerializer(serializers.ModelSerializer):
    """List event-level participants"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    shopper_name = serializers.CharField(source='shopper.get_full_name', read_only=True)
    shopper_email = serializers.EmailField(source='shopper.email', read_only=True)
    shopper_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = EventParticipant
        fields = [
            'id', 'event', 'shopper', 'event_name', 'shopper_name', 'shopper_email',
            'participant_name', 'participant_email', 'participant_phone', 'contact_number',
            'status', 'created_at', 'shopper_avatar'
        ]
        read_only_fields = ['id', 'created_at', 'status']
    
    def get_shopper_avatar(self, obj):
        """Get shopper avatar with null checks"""
        request = self.context.get('request')
        
        if not obj.shopper or not hasattr(obj.shopper, 'profile'):
            return None
        
        if not obj.shopper.profile.profile_picture:
            return None
        
        if request:
            return request.build_absolute_uri(obj.shopper.profile.profile_picture.url)
        
        return obj.shopper.profile.profile_picture.url


class EventParticipantCreateSerializer(serializers.ModelSerializer):
    """Shopper creates event participation request"""
    
    class Meta:
        model = EventParticipant
        fields = [
            'event', 'participant_name', 'participant_email',
            'participant_phone', 'contact_number'
        ]
    
    def validate_participant_email(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value
    
    def validate(self, data):
        """Check if shopper already has a participation request for this event"""
        user = self.context.get('request').user
        event = data.get('event')
        
        if EventParticipant.objects.filter(event=event, shopper=user).exists():
            raise serializers.ValidationError(
                "You have already submitted a participation request for this event"
            )
        return data
    
    def create(self, validated_data):
        # Get the user from context (passed from the view)
        user = self.context.get('request').user
        validated_data['shopper'] = user
        validated_data.setdefault('status', 'pending')
        return super().create(validated_data)


class EventParticipantDetailSerializer(serializers.ModelSerializer):
    """Detailed event participant view"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_location = serializers.CharField(source='event.location', read_only=True)
    event_from_date = serializers.DateField(source='event.from_date', read_only=True)
    event_to_date = serializers.DateField(source='event.to_date', read_only=True)
    shopper_name = serializers.CharField(source='shopper.get_full_name', read_only=True)
    shopper_email = serializers.EmailField(source='shopper.email', read_only=True)
    
    class Meta:
        model = EventParticipant
        fields = [
            'id', 'event', 'shopper', 'event_name', 'event_location',
            'event_from_date', 'event_to_date', 'shopper_name', 'shopper_email',
            'participant_name', 'participant_email', 'participant_phone', 'contact_number',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status']


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
            'is_visited', 'total_visits', 'total_check_ins', 'created_at'
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
            'is_visited', 'total_visits', 'total_check_ins', 'created_at', 'updated_at'
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
    shopper_name = serializers.CharField(source='shopper.profile.name', read_only=True)
    shopper_phone = serializers.CharField(source='shopper.profile.phone', read_only=True)
    shopper_email = serializers.EmailField(source='shopper.email', read_only=True)
    event_name = serializers.CharField(source='event_passport.event.name', read_only=True)
    shop_name = serializers.CharField(source='event_passport.shop.shop_name', read_only=True)
    passport_id = serializers.CharField(source='event_passport.passport_id', read_only=True)
    
    class Meta:
        model = ShopperCheckIn
        fields = [
            'id', 'event_passport', 'shopper', 'shopper_name',
            'shopper_phone', 'shopper_email', 'event_name', 'shop_name', 'passport_id',
            'status', 'check_in_time', 'created_at'
        ]
        read_only_fields = ['id', 'check_in_time', 'created_at', 'status']


class CheckInDetailSerializer(serializers.ModelSerializer):
    """Detailed check-in view"""
    shopper_name = serializers.CharField(source='shopper.profile.name', read_only=True)
    shopper_phone = serializers.CharField(source='shopper.profile.phone', read_only=True)
    shopper_email = serializers.EmailField(source='shopper.email', read_only=True)
    event_passport_details = PassportDetailSerializer(source='event_passport', read_only=True)
    
    class Meta:
        model = ShopperCheckIn
        fields = [
            'id', 'event_passport', 'shopper', 'shopper_name',
            'shopper_phone', 'shopper_email', 'event_passport_details', 'status',
            'check_in_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'check_in_time', 'created_at', 'updated_at', 'status']


class CheckInCreateSerializer(serializers.ModelSerializer):
    """Create check-in (shopper scans QR)"""
    
    class Meta:
        model = ShopperCheckIn
        fields = ['event_passport', 'shopper']
    
    def validate(self, data):
        # Check if shopper already checked in to this passport
        # if ShopperCheckIn.objects.filter(
        #     event_passport=data['event_passport'],
        #     shopper=data['shopper']
        # ).exists():
        #     raise serializers.ValidationError('Already checked in to this location')
        
        # Check if passport is valid
        from datetime import date
        passport = data['event_passport']
        today = date.today()
        
        if passport.valid_from and today < passport.valid_from:
            raise serializers.ValidationError('Passport not yet valid')
        
        if passport.valid_to and today > passport.valid_to:
            raise serializers.ValidationError('Passport has expired')
        
        return data


class EventApproveRejectSerializer(serializers.Serializer):
    """Superadmin approves or rejects event"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    
    def validate_action(self, value):
        if value not in ['approve', 'reject']:
            raise serializers.ValidationError("Action must be 'approve' or 'reject'")
        return value


class ShopPassportWithCheckInSerializer(serializers.ModelSerializer):
    """Serializer for passports with check-in status for shopper"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    shop_location = serializers.CharField(source='shop.shop_location', read_only=True)
    shop_phone = serializers.CharField(source='shop.contact_person_phone', read_only=True)
    shop_logo = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()
    passport_qr_id = serializers.CharField(source='passport_id', read_only=True)
    is_visited = serializers.SerializerMethodField()
    check_in_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EventPassport
        fields = [
            'id', 'passport_qr_id', 'shop_id', 'shop_name', 'shop_location',
            'shop_logo', 'shop_phone', 'qr_code_url', 'is_visited', 'check_in_count',
            'valid_from', 'valid_to'
        ]
        read_only_fields = fields
    
    def get_shop_logo(self, obj):
        request = self.context.get('request')
        if obj.shop.shop_logo and request:
            return request.build_absolute_uri(obj.shop.shop_logo.url)
        return None
    
    def get_qr_code_url(self, obj):
        request = self.context.get('request')
        if obj.shop_qr_code and request:
            return request.build_absolute_uri(obj.shop_qr_code.url)
        return None
    
    def get_is_visited(self, obj):
        """Check if shopper checked in to this passport"""
        request = self.context.get('request')
        if request and request.user:
            return ShopperCheckIn.objects.filter(
                event_passport=obj,
                shopper=request.user
            ).exists()
        return False
    
    def get_check_in_count(self, obj):
        """Count check-ins for this shopper to this passport"""
        request = self.context.get('request')
        if request and request.user:
            return ShopperCheckIn.objects.filter(
                event_passport=obj,
                shopper=request.user
            ).count()
        return 0


class AcceptedEventWithShopsSerializer(serializers.ModelSerializer):
    """Serializer for accepted events with shops and check-in status"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_location = serializers.CharField(source='event.location', read_only=True)
    event_image = serializers.SerializerMethodField()
    event_from_date = serializers.DateField(source='event.from_date', read_only=True)
    event_to_date = serializers.DateField(source='event.to_date', read_only=True)
    event_status = serializers.CharField(source='event.status', read_only=True)
    shops = serializers.SerializerMethodField()
    total_shops = serializers.SerializerMethodField()
    total_visited_shops = serializers.SerializerMethodField()
    participation_status = serializers.CharField(source='status', read_only=True)
    
    class Meta:
        model = EventParticipant
        fields = [
            'id', 'event', 'event_name', 'event_location', 'event_image',
            'event_from_date', 'event_to_date', 'event_status', 
            'participation_status', 'shops', 'total_shops', 'total_visited_shops',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_event_image(self, obj):
        """Get event image"""
        request = self.context.get('request')
        if obj.event.image and request:
            return request.build_absolute_uri(obj.event.image.url)
        return None
    
    def get_shops(self, obj):
        """Get all shops in this event with check-in status"""
        passports = EventPassport.objects.filter(event=obj.event)
        serializer = ShopPassportWithCheckInSerializer(
            passports,
            many=True,
            context=self.context
        )
        return serializer.data
    
    def get_total_shops(self, obj):
        """Total shops in event"""
        return EventPassport.objects.filter(event=obj.event).count()
    
    def get_total_visited_shops(self, obj):
        """How many shops shopper visited in this event"""
        request = self.context.get('request')
        if request and request.user:
            return ShopperCheckIn.objects.filter(
                event_passport__event=obj.event,
                shopper=request.user
            ).values('event_passport__shop').distinct().count()
        return 0


# ==================== SHOP OWNER: MY EVENTS WITH CHECK-INS ====================

class CheckInUserSerializer(serializers.ModelSerializer):
    """Serializer for users who checked in"""
    shopper_name = serializers.CharField(source='shopper.profile.name', read_only=True)
    shopper_phone = serializers.CharField(source='shopper.profile.phone', read_only=True)
    shopper_email = serializers.EmailField(source='shopper.email', read_only=True)
    shopper_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopperCheckIn
        fields = ['id', 'shopper_id', 'shopper_name', 'shopper_phone', 'shopper_email', 'shopper_avatar', 'check_in_time', 'status']
        read_only_fields = fields
    
    def get_shopper_avatar(self, obj):
        request = self.context.get('request')
        if obj.shopper and hasattr(obj.shopper, 'profile') and obj.shopper.profile.profile_picture:
            if request:
                return request.build_absolute_uri(obj.shopper.profile.profile_picture.url)
        return None


class ShopWithCheckInsSerializer(serializers.ModelSerializer):
    """Serializer for shop with check-in users"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    shop_location = serializers.CharField(source='shop.shop_location', read_only=True)
    shop_phone = serializers.CharField(source='shop.contact_person_phone', read_only=True)
    shop_logo = serializers.SerializerMethodField()
    passport_qr_id = serializers.CharField(source='passport_id', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    check_ins = serializers.SerializerMethodField()
    total_check_ins = serializers.SerializerMethodField()
    unique_visitors = serializers.SerializerMethodField()
    
    class Meta:
        model = EventPassport
        fields = [
            'id', 'shop_id', 'shop_name', 'shop_location', 'shop_logo',
            'passport_qr_id', 'shop_phone', 'qr_code_url', 'total_check_ins', 'unique_visitors',
            'check_ins', 'valid_from', 'valid_to'
        ]
        read_only_fields = fields
    
    def get_shop_logo(self, obj):
        request = self.context.get('request')
        if obj.shop.shop_logo and request:
            return request.build_absolute_uri(obj.shop.shop_logo.url)
        return None
    
    def get_qr_code_url(self, obj):
        request = self.context.get('request')
        if obj.shop_qr_code and request:
            return request.build_absolute_uri(obj.shop_qr_code.url)
        return None
    
    def get_check_ins(self, obj):
        """List all users who checked in to this shop"""
        check_ins = ShopperCheckIn.objects.filter(event_passport=obj).order_by('-check_in_time')
        serializer = CheckInUserSerializer(check_ins, many=True, context=self.context)
        return serializer.data
    
    def get_total_check_ins(self, obj):
        return ShopperCheckIn.objects.filter(event_passport=obj).count()
    
    def get_unique_visitors(self, obj):
        return ShopperCheckIn.objects.filter(
            event_passport=obj
        ).values('shopper').distinct().count()


class ShopOwnerEventWithShopsSerializer(serializers.ModelSerializer):
    """Serializer for shop owner's event with their shops and check-ins"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_location = serializers.CharField(source='event.location', read_only=True)
    event_image = serializers.SerializerMethodField()
    event_from_date = serializers.DateField(source='event.from_date', read_only=True)
    event_to_date = serializers.DateField(source='event.to_date', read_only=True)
    event_status = serializers.CharField(source='event.status', read_only=True)
    shops = serializers.SerializerMethodField()
    total_shops = serializers.SerializerMethodField()
    total_check_ins = serializers.SerializerMethodField()
    
    class Meta:
        model = EventShop
        fields = [
            'id', 'event', 'event_name', 'event_location', 'event_image',
            'event_from_date', 'event_to_date', 'event_status', 'status',
            'shops', 'total_shops', 'total_check_ins', 'created_at'
        ]
        read_only_fields = fields
    
    def get_event_image(self, obj):
        request = self.context.get('request')
        if obj.event.image and request:
            return request.build_absolute_uri(obj.event.image.url)
        return None
    
    def get_shops(self, obj):
        """Get shop with check-ins (only this shop from this event)"""
        passport = EventPassport.objects.filter(event=obj.event, shop=obj.shop).first()
        if passport:
            serializer = ShopWithCheckInsSerializer(passport, context=self.context)
            return [serializer.data]
        return []
    
    def get_total_shops(self, obj):
        """Total shops owned by this shop owner in this event"""
        return EventShop.objects.filter(
            event=obj.event,
            shop__shop_owner=obj.shop.shop_owner
        ).count()
    
    def get_total_check_ins(self, obj):
        """Total check-ins for all shops of this owner in this event"""
        return ShopperCheckIn.objects.filter(
            event_passport__event=obj.event,
            event_passport__shop__shop_owner=obj.shop.shop_owner
        ).count()


# ==================== EVENT ADMIN: MY EVENTS WITH ALL CHECK-INS ====================

class EventAdminEventWithCheckInsSerializer(serializers.ModelSerializer):
    """Serializer for event admin's event with all shops and check-ins"""
    admin_name = serializers.CharField(source='shop_admin.get_full_name', read_only=True)
    event_images = serializers.SerializerMethodField()  # plural
    shops_with_checkins = serializers.SerializerMethodField()
    total_shops = serializers.SerializerMethodField()
    total_check_ins = serializers.SerializerMethodField()
    total_unique_visitors = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'about_the_event', 'location', 'latitude', 'longitude',
            'from_date', 'to_date', 'admin_name', 'event_images',
            'shops_with_checkins', 'total_shops', 'total_check_ins', 'total_unique_visitors',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_event_images(self, obj):  # Changed from get_event_image to get_event_images
        request = self.context.get('request')
        # Get all images from the related EventImage model
        event_images = obj.images.all()
        if event_images and request:
            return [request.build_absolute_uri(img.image.url) for img in event_images]
        return []
        
    def get_shops_with_checkins(self, obj):
        """Get all shops in event with their check-ins"""
        passports = EventPassport.objects.filter(event=obj)
        serializer = ShopWithCheckInsSerializer(passports, many=True, context=self.context)
        return serializer.data
    
    def get_total_shops(self, obj):
        return EventPassport.objects.filter(event=obj).count()
    
    def get_total_check_ins(self, obj):
        return ShopperCheckIn.objects.filter(event_passport__event=obj).count()
    
    def get_total_unique_visitors(self, obj):
        return ShopperCheckIn.objects.filter(
            event_passport__event=obj
        ).values('shopper').distinct().count()