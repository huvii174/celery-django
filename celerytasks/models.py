from __future__ import unicode_literals
from django_celery_beat.models import PeriodicTask, CrontabSchedule

from uuid import uuid4

from django.db import models


class ScheduleJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    job_action = models.TextField(max_length=500, blank=False, null=False)
    rrule_str = models.TextField(max_length=500, blank=False, null=False)
    start_date = models.DateTimeField(blank=False, null=False)
    end_date = models.DateTimeField(blank=False, null=False)
    max_run = models.IntegerField(blank=False, null=False)


class ScheduledTask(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    task_id = models.ForeignKey(PeriodicTask, on_delete=models.CASCADE)
    job_id = models.ForeignKey(ScheduleJob, on_delete=models.CASCADE)

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
    run_duration = models.DurationField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


models.deletion.PROTECT
