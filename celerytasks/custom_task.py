from celery import Task
from celerytasks.models import TaskDetail, JobSettings
from logger import get_logger
import requests
from django_celery_beat.models import PeriodicTask
from .views import convert_task_detail_to_log_data

logger = get_logger()


class RepeatTask(Task):
    """Base task for executing repeated tasks."""

    def __call__(self, *args, **kwargs):
        job_id = args[2]
        job_settings = JobSettings.objects.filter(job_id=job_id).first()
        if job_settings is None:
            logger.error(f'JobSettings not found for job_id {job_id}.')
            return None
        try:
            result = super(RepeatTask, self).__call__(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f'Error in task {self.name}: {e}')
            job_settings.increase_failure_count()
            enable_retry = job_settings.restart_on_failure
            if enable_retry:
                max_retries = job_settings.max_failure
                time_limit = job_settings.max_run_duration.total_seconds()
                retry_delay = float(job_settings.retry_delay)
                self.retry(exc=e, countdown=retry_delay, args=args, kwargs=kwargs, max_retries=max_retries,
                           time_limit=time_limit)
            else:
                raise Exception(f'Error in task {self.name}: {e}')

    def before_start(self, task_id, args, kwargs):
        logger.info(f'Hook before_start for task with id: {task_id}')
        try:
            task_name = args[1]
            run_account = args[3]
            next_run_date = args[4]
            task_detail = TaskDetail.objects.filter(task_name=task_name).first()
            if task_detail is None:
                logger.error(f'TaskDetail not found for task_name {task_name}.')
            task_detail.start_running(task_id, run_account)
            periodic_task = PeriodicTask.objects.filter(name=task_name).first()
            if periodic_task is None:
                logger.error(f'PeriodicTask not found for task_name {task_name}.')
                return
        except Exception as e:
            logger.error(f'Error in before_start for {task_id}: {e}')
            return

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f'Hook on_success for task with id: {task_id}')
        try:
            task_detail = TaskDetail.objects.filter(celery_task_id=task_id).first()
            if task_detail is None:
                logger.error(f'TaskDetail not found for task_id {task_id}.')
                return
            task_detail.count_duration()
            task_detail.save_status(TaskDetail.STATUS_SUCCESS)
        except Exception as e:
            logger.error(f'Error in task {self.name}: {e}')

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.info(f'Hook on_failure for task with id: {task_id}')
        try:
            task_detail = TaskDetail.objects.filter(celery_task_id=task_id).first()
            if task_detail is None:
                logger.error(f'TaskDetail not found for task_id {task_id}.')
                return
            task_detail.save_status(TaskDetail.STATUS_FAILURE)
            logger.error(f'Task {task_id}: {exc} marked as FAILURE')
        except Exception as e:
            logger.error(f'Error in task {self.name}: {e}')
            return

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.info(f'Hook on_retry for task with id: {task_id}')
        try:
            task_name = args[1]
            task_detail = TaskDetail.objects.filter(celery_task_id=task_id).first()
            if task_detail is None:
                logger.error(f'TaskDetail not found for task_id {task_id}.')
                return
            task_detail.save_status(TaskDetail.STATUS_RUNNING)
            job_settings = JobSettings.objects.filter(job_id=task_detail.job_id).first()
            if job_settings is None:
                logger.error(f'JobSettings not found for job_id {task_detail.job_id}.')
                return
            job_settings.increase_retry_count()
            logger.info(f'Retrying task {task_name} for job {job_settings.job_id}.')
        except Exception as e:
            logger.error(f'Error in on_retry for {task_id}: {e}')
            return

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        logger.info(f'Hook after_return for task with id: {task_id}')
        try:
            task_detail = TaskDetail.objects.filter(celery_task_id=task_id).first()
            if task_detail is None:
                logger.error(f'TaskDetail not found for task_id {task_id}.')
                return
            job_settings = JobSettings.objects.filter(job_id=task_detail.job_id).first()
            if job_settings is None:
                logger.error(f'JobSettings not found for job_id {task_detail.job_id}.')
                return
            job_settings.increase_run_count()
        except Exception as e:
            logger.error(f'Error in after_return for {task_id}: {e}')