from django.db import models
from apps.accounts.models import User
from apps.shop.models import Shop


class Event(models.Model):
    shop_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    about_the_event = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.CharField(max_length=100, blank=True, null=True)
    longitude = models.CharField(max_length=100, blank=True, null=True)
    from_date = models.DateField(blank=True, null=True)
    to_date = models.DateField(blank=True, null=True)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to="shopadmin/event_images/", blank=True, null=True)

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name if self.name else "Unnamed Event"
    
    class Meta: 
        verbose_name = "Create Event"
        verbose_name_plural = "Create Events"
        
class EventImage(models.Model):
    event = models.ForeignKey(Event, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='shopadmin/event_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.event.name} uploaded at {self.uploaded_at}"

    class Meta:
        ordering = ['uploaded_at']

class EventShop(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_shops', blank=True, null=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='event_shops', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event.name} - {self.shop.shop_name} ({self.status})"


class EventParticipant(models.Model):
    """Event-level participation - shopper requests to join event"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_participants', blank=True, null=True)
    shopper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_participant_requests', blank=True, null=True)
    participant_name = models.CharField(max_length=255, blank=True, null=True)
    participant_email = models.EmailField(max_length=255, blank=True, null=True)
    participant_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Event Participant"
        verbose_name_plural = "Event Participants"
        unique_together = ('event', 'shopper')  # One participation per event per shopper

    def __str__(self):
        return f"{self.participant_name or self.shopper.username} - {self.event.name}"


class EventShopParticipant(models.Model):
    event_shop = models.ForeignKey(EventShop, on_delete=models.CASCADE, related_name='participants', blank=True, null=True)
    shopper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_participations', blank=True, null=True)
    participant_name = models.CharField(max_length=255, blank=True, null=True)
    participant_email = models.EmailField(max_length=255, blank=True, null=True)
    participant_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.participant_name if self.participant_name else "Unnamed Participant"
    
    class Meta:
        verbose_name = "Event Participant"
        verbose_name_plural = "Event Participants"


class EventPassport(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='passports', blank=True, null=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='passports', blank=True, null=True)
    passport_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    shop_qr_code = models.ImageField(upload_to="shop/qr_codes/", blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    valid_from = models.DateField(blank=True, null=True)
    valid_to = models.DateField(blank=True, null=True)
    
    # Track if shop has been visited
    is_visited = models.BooleanField(default=False)
    total_visits = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.passport_id
    
    class Meta:
        verbose_name = "Shop Passport"
        verbose_name_plural = "Shop Passports"

class ShopperCheckIn(models.Model):
    STATUS_CHOICES = [
        ('stamped', 'Stamped'),
        ('visited', 'Visited'),
    ]
    
    event_passport = models.ForeignKey(EventPassport, on_delete=models.CASCADE, related_name='check_ins', blank=True, null=True)
    shopper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='check_ins', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='stamped')
    check_in_time = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        shopper_name = self.shopper.get_full_name() or self.shopper.username
        return f"{shopper_name} - {self.event_passport.passport_id} ({self.status})"
    
    class Meta:
        verbose_name = "Shopper Check-In"
        verbose_name_plural = "Shopper Check-Ins"