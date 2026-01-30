"""
Signals for auto-generating passports and handling related actions
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from .models import EventShop, EventPassport
import uuid
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=EventShop)
def auto_create_passport_on_shop_approval(sender, instance, created, update_fields, **kwargs):
    """
    Auto-create EventPassport with QR code when shop request is approved
    """
    try:
        logger.info(f"Signal fired for EventShop {instance.id}, status={instance.status}, update_fields={update_fields}")
        
        # Check if status was just changed to 'accepted'
        # Note: update_fields might be None, so check instance.status directly
        if instance.status == 'accepted':
            # Check if passport already exists
            existing_passport = EventPassport.objects.filter(
                event=instance.event,
                shop=instance.shop
            ).exists()
            
            if existing_passport:
                logger.info(f"Passport already exists for EventShop {instance.id}")
                return
            
            logger.info(f"Creating passport for EventShop {instance.id}")
            
            # Generate unique passport ID
            passport_id = f"{instance.event.id}-{instance.shop.id}-{uuid.uuid4().hex[:8]}"
            
            # Create EventPassport
            passport = EventPassport.objects.create(
                event=instance.event,
                shop=instance.shop,
                passport_id=passport_id,
                description=f"Passport for {instance.shop.shop_name} at {instance.event.name}",
                valid_from=instance.event.from_date,
                valid_to=instance.event.to_date
            )
            print("hello ....................passport created", passport.valid_from , passport.valid_to)
            
            logger.info(f"Passport created: {passport.id}, now generating QR code")
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(passport_id)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to BytesIO
            img_io = BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            
            # Save to passport
            filename = f"qr-{passport_id}.png"
            passport.shop_qr_code.save(filename, ContentFile(img_io.read()), save=True)
            
            logger.info(f"QR code saved for passport {passport.id}")
            
    except Exception as e:
        logger.error(f"Error in auto_create_passport_on_shop_approval: {str(e)}", exc_info=True)
        
        # Save to passport
        filename = f"qr-{passport_id}.png"
        passport.shop_qr_code.save(filename, ContentFile(img_io.read()), save=True)
