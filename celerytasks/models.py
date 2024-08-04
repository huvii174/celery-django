from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django_celery_beat.models import PeriodicTask


class JobSettings(models.Model):
    job_id = models.CharField(max_length=255, primary_key=True)
    queue_name = models.CharField(max_length=255, blank=True, null=True)
    function_name = models.CharField(max_length=255, blank=False, null=False)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    repeat_interval = models.TextField(max_length=4000, blank=True, null=True)
    max_run_duration = models.DurationField(blank=True, null=True)
    max_run = models.IntegerField(blank=True, null=True)
    max_failure = models.IntegerField(blank=True, null=True)
    retry_delay = models.IntegerField(blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)
    is_enable = models.BooleanField(default=False)
    auto_drop = models.BooleanField(default=False)
    restart_on_failure = models.BooleanField(default=False)
    restartable = models.BooleanField(default=False)
    run_account = models.CharField(max_length=255, blank=True, null=True)

    class JobTypeEnum(models.TextChoices):
        REST_API = 'REST_API', 'REST API'
        EXECUTABLE = 'EXECUTABLE', 'Executable'

    job_type = models.CharField(max_length=50, choices=JobTypeEnum.choices)
    job_action = models.TextField(blank=True, null=True)
    run_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    retry_count = models.IntegerField(default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def increase_run_count(self):
        self.run_count += 1
        self.save(update_fields=('run_count',))
        return self

    def increase_failure_count(self):
        self.failure_count += 1
        self.save(update_fields=('failure_count',))
        return self

    def increase_retry_count(self):
        self.retry_count += 1
        self.save(update_fields=('retry_count',))
        return self

    class Meta:
        db_table = 'celery_job_settings'


class TaskDetail(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    job = models.ForeignKey(JobSettings, on_delete=models.CASCADE)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    run_duration = models.DurationField(blank=True, null=True)
    run_date = models.DateTimeField(blank=False, null=False)
    task_name = models.CharField(max_length=255, blank=False, null=False)
    run_account = models.CharField(max_length=255, blank=True, null=True)

    STATUS_CREATED = 'created'
    STATUS_RUNNING = 'running'
    STATUS_SUCCESS = 'success'
    STATUS_FAILURE = 'failure'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_CREATED, 'Created'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILURE, 'Failure'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    status = models.CharField(max_length=255, choices=STATUS_CHOICES,
                              default=STATUS_CREATED)

    def save_status(self, status):
        """Sets and saves the status to the scheduled task.

        Arguments:
            status (str): Status.

        Returns:
            ScheduledTask: Current scheduled task instance.
        """
        self.status = status
        self.save(update_fields=('status',))
        return self

    def start_running(self, task_id, run_account):
        self.run_date = timezone.now()
        self.celery_task_id = task_id
        self.status = self.STATUS_RUNNING
        self.run_account = run_account
        self.save(update_fields=('run_date', 'status', 'celery_task_id', 'run_account'))
        return self

    def count_duration(self):
        now = timezone.now()
        self.run_duration = now - self.run_date
        self.save()
        return self

    class Meta:
        db_table = 'celery_task_detail'