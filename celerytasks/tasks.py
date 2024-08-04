from celery import shared_task
from datetime import date
from .custom_task import RepeatTask
from logger import get_logger
import time

logger = get_logger()


@shared_task(bind=True, base=RepeatTask)
def rest_api(self, job_action, job_name, job_id, run_account, next_run_date):
    time.sleep(30.0)
    return f'{run_account} trigger REST_API action: {job_action} at {date.today()}'


@shared_task(bind=True, base=RepeatTask)
def executable(self, job_action, job_name, job_id, run_account, next_run_date):
    # time.sleep(30.0)
    raise Exception('Error in executable task')
    # return f'Executable action: {job_action} at {date.today()}'