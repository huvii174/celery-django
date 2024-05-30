from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from . import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'batchbe.settings')

app = Celery('batchbe')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.beat_schedule = {
    'add-every-30-seconds': {
        'task': 'celerytasks.tasks.add',
        'schedule': 30.0,
        'args': (16, 16)
    },
}
