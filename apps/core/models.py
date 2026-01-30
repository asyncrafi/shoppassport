from django.db import models

class AppSettings(models.Model):
    SETTING_TYPES = [
        ('privacy_policy', 'Privacy Policy'),
        ('terms_conditions', 'Terms & Conditions'),
        ('about_us', 'About Us'),
    ]

    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, unique=True)
    content = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return dict(self.SETTING_TYPES).get(self.setting_type)


class CommonData(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    image_one = models.ImageField(upload_to='common_data/images/', blank=True, null=True)
    image_two = models.ImageField(upload_to='common_data/images/', blank=True, null=True)
    image_three = models.ImageField(upload_to='common_data/images/', blank=True, null=True)
    image_four = models.ImageField(upload_to='common_data/images/', blank=True, null=True)

    def __str__(self):
        return self.name
