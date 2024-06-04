from django.shortcuts import render
from django.http import JsonResponse
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json
from django.views.decorators.csrf import csrf_exempt
from celery import current_app

@csrf_exempt
def create_interval_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_name = data.get('task_name', 'celerytasks.tasks.add')
        interval = data.get('interval', 10)
        args = data.get('args', [4, 4])

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=interval,
            period=IntervalSchedule.SECONDS,
        )

        PeriodicTask.objects.create(
            interval=schedule,
            name=f'{task_name}-{interval}',
            task=task_name,
            args=json.dumps(args),
        )
        return JsonResponse({'status': 'success', 'message': 'Task scheduled successfully.'})

    return JsonResponse({'status': 'failure', 'message': 'Invalid request method.'})


@csrf_exempt
def create_cron_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_name = data.get('task_name', 'celerytasks.tasks.add')
        minute = data.get('minute', '*')
        hour = data.get('hour', '*')
        day_of_week = data.get('day_of_week', '*')
        day_of_month = data.get('day_of_month', '*')
        month_of_year = data.get('month_of_year', '*')
        args = data.get('args', [4, 4])

        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
        )

        PeriodicTask.objects.create(
            crontab=schedule,
            name=f'{task_name}-{minute}-{hour}-{day_of_week}-{day_of_month}-{month_of_year}',
            task=task_name,
            args=json.dumps(args),
        )
        return JsonResponse({'status': 'success', 'message': 'Task scheduled successfully.'})

    return JsonResponse({'status': 'failure', 'message': 'Invalid request method.'})


@csrf_exempt
def update_task(request, task_id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        task = PeriodicTask.objects.get(id=task_id)

        task_name = data.get('task_name', task.task)
        args = data.get('args', json.loads(task.args))

        task.task = task_name
        task.args = json.dumps(args)
        task.save()

        if 'interval' in data:
            interval = data.get('interval')
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=interval,
                period=IntervalSchedule.SECONDS,
            )
            task.interval = schedule
            task.crontab = None
            task.save()

        if 'minute' in data or 'hour' in data or 'day_of_week' in data or 'day_of_month' in data or 'month_of_year' in data:
            minute = data.get('minute', task.crontab.minute)
            hour = data.get('hour', task.crontab.hour)
            day_of_week = data.get('day_of_week', task.crontab.day_of_week)
            day_of_month = data.get('day_of_month', task.crontab.day_of_month)
            month_of_year = data.get('month_of_year', task.crontab.month_of_year)

            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=minute,
                hour=hour,
                day_of_week=day_of_week,
                day_of_month=day_of_month,
                month_of_year=month_of_year,
            )
            task.crontab = schedule
            task.interval = None
            task.save()

        return JsonResponse({'status': 'success', 'message': 'Task updated successfully.'})

    return JsonResponse({'status': 'failure', 'message': 'Invalid request method.'})


@csrf_exempt
def delete_task(request, task_id):
    if request.method == 'DELETE':
        task = PeriodicTask.objects.get(id=task_id)
        task.delete()
        return JsonResponse({'status': 'success', 'message': 'Task deleted successfully.'})

    return JsonResponse({'status': 'failure', 'message': 'Invalid request method.'})

@csrf_exempt
def assign_task_to_worker(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_name = data.get('task_name')
        worker_id = data.get('worker_id')
        args = data.get('args', [])

        if not task_name or not worker_id:
            return JsonResponse({'status': 'failure', 'message': 'Task name and worker ID are required.'})

        queue_name = f'worker_{worker_id}_queue'

        # Send task to the specified worker's queue
        current_app.send_task(task_name, args=args, queue=queue_name)

        return JsonResponse({'status': 'success', 'message': f'Task {task_name} assigned to worker {worker_id}.'})

    return JsonResponse({'status': 'failure', 'message': 'Invalid request method.'})

@csrf_exempt
def health_check(request):
    return JsonResponse({"status": "ok"})
