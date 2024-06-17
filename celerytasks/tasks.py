from celery import shared_task
from .custom_task import RepeatTask
import time


@shared_task(bind=True, base=RepeatTask)
def add(self, x, y):
    time.sleep(30)
    return x + y
