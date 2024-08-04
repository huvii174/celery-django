from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from batchbe import settings
from logger import get_logger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'batchbe.settings')

app = Celery('batchbe')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(['celerytasks'])