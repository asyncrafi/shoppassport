from django.db import models
from apps.accounts.models import User

class Shop(models.Model):
    shop_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops', blank=True, null=True)
    shop_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    shop_location = models.CharField(max_length=255, blank=True, null=True)
    shop_logo = models.ImageField(upload_to="shop/logos/", blank=True, null=True)
    about_the_shop = models.TextField(blank=True, null=True)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person_phone = models.CharField(max_length=20, blank=True, null=True)
    cover_image = models.ImageField(upload_to="shop/cover_images/", blank=True, null=True)
    upload_pdf_pattern = models.FileField(upload_to="shop/pdf_patterns/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_name if self.shop_name else "Unnamed Shop"
    
    class Meta:
        verbose_name = "Shop"
        verbose_name_plural = "Shops"

