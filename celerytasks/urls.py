from django.urls import path
from .views import create_interval_task, create_cron_task, update_task, delete_task

urlpatterns = [
    path('create_interval_task/', create_interval_task, name='create_interval_task'),
    path('create_cron_task/', create_cron_task, name='create_cron_task'),
    path('update_task/<int:task_id>/', update_task, name='update_task'),
    path('delete_task/<int:task_id>/', delete_task, name='delete_task'),
]
