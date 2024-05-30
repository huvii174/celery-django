from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from batchbe import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'batchbe.settings')

app = Celery('batchbe')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.task_queues = {
    'worker_1_queue': {
        'exchange': 'worker_1_queue',
        'exchange_type': 'direct',
        'binding_key': 'worker_1_queue',
    },
    'worker_2_queue': {
        'exchange': 'worker_2_queue',
        'exchange_type': 'direct',
        'binding_key': 'worker_2_queue',
    },
    'worker_3_queue': {
        'exchange': 'worker_3_queue',
        'exchange_type': 'direct',
        'binding_key': 'worker_3_queue',
    },
}

app.conf.task_routes = {
    'celerytasks.tasks.add': {'queue': 'worker_1_queue'},
    # Add more task routes here as needed
}
