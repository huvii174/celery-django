from django.http import JsonResponse
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule, ClockedSchedule
import json
from django.views.decorators.csrf import csrf_exempt
from celery import current_app
from dateutil.rrule import rrulestr
from django.utils import timezone
from datetime import datetime
from .models import ScheduleJob, ScheduledTask
from batchbe.celery import app
from celery.result import AsyncResult


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
def force_terminate_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('task_id')
        result = AsyncResult(task_id, app=app)
        result.revoke(terminate=True, signal='SIGKILL')
        return JsonResponse({'status': 'Task terminated'})


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
def rrule_schedule_task(request):
    if request.method == 'POST':
        try:
            # Parse JSON request body
            data = json.loads(request.body)
            rrule_str = data['rrule_string']
            start_date = timezone.make_aware(datetime.fromisoformat(data['start_date']))
            end_date = timezone.make_aware(datetime.fromisoformat(data['end_date']))
            run_count = data['run_count']
            job_action = data['job_action']
            arg = json.dumps([4, 4])

            schedule_job, created = ScheduleJob.objects.get_or_create(job_action=job_action, rrule_str=rrule_str,
                                                                      start_date=start_date, end_date=end_date,
                                                                      max_run=run_count)
            if not created:
                schedule_job.save()

            # Calculate the next run times
            next_runs = get_next_runs(rrule_str, run_count, start_date, end_date)

            # Create a ClockedSchedule for each run time
            clocked_schedules = []
            for next_run in next_runs:
                clocked_schedule = ClockedSchedule.objects.create(clocked_time=next_run)
                clocked_schedules.append(clocked_schedule)

            # Create PeriodicTask for each ClockedSchedule
            tasks = []
            for i, clocked_schedule in enumerate(clocked_schedules):
                task_name = f'Clocked Task {i + 1} at {clocked_schedule.clocked_time} {rrule_str}'
                task, created = PeriodicTask.objects.get_or_create(
                    clocked=clocked_schedule,
                    name=task_name,
                    task='celerytasks.tasks.add',
                    args=arg,
                    defaults={'one_off': True}
                )
                if not created:
                    task.clocked = clocked_schedule
                    task.enabled = True
                    task.description = schedule_job.id
                    task.save()

                tasks.append(task)

                schedule_task, created = ScheduledTask.objects.get_or_create(task_id=task, job_id=schedule_job,
                                                                             status=ScheduledTask.STATUS_CREATED)

                if not created:
                    schedule_task.save()

            return JsonResponse({'status': 'success', 'tasks': [task.id for task in tasks]})
        except KeyError as e:
            return JsonResponse({'status': 'error', 'message': f'Missing parameter: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def get_next_runs(rrule_str, run_count, start_date, end_date):
    """
    Calculate the next run times based on the input rrule string, start date, and run count.

    :param rrule_str: The recurrence rule string (RFC 2445 format).
    :param run_count: The number of next occurrences to find.
    :param start_date: The start datetime for the recurrence rule.
    :param end_date: The end datetime for the recurrence rule.
    :return: A list of next run datetimes.
    """
    rule = rrulestr(rrule_str, dtstart=start_date)
    next_runs = []

    current_time = start_date
    for _ in range(run_count):
        next_run = rule.after(current_time)
        if next_run is None or next_run > end_date:
            break
        next_runs.append(next_run)
        current_time = next_run

    return next_runs


@csrf_exempt
def health_check(request):
    return JsonResponse({"status": "ok"})
