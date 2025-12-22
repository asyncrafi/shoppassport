from django.apps import AppConfig


class ShopadminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shopadmin'
    
    def ready(self):
        import apps.shopadmin.signals
