import os
from celery import Celery
from celery.schedules import crontab
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Initialize Django before autodiscovering tasks
django.setup()

# Beat schedule configuration
app.conf.beat_schedule = {
    'process-scheduled-notifications': {
        'task': 'apps.notification.tasks.process_scheduled_notifications',
        'schedule': crontab(minute='*'),
    },
}

app.conf.timezone = 'UTC'

# This will discover tasks after Django is properly initialized
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')