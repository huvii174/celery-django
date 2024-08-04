from django.urls import path
from .views import (health_check, rrule_schedule_task, manually_run, force_terminate_task, update_job)

urlpatterns = [
    path('create_rrule_task/', rrule_schedule_task, name='rrule_schedule_task'),
    path('force_stop/', force_terminate_task, name='force_stop'),
    path('manually_run/', manually_run, name='manually_run'),
    path('health/', health_check, name='health_check'),
    path('update_job/', update_job, name='update_job'),
]