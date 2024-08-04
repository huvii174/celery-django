from django.http import JsonResponse
from django_celery_beat.models import PeriodicTask, ClockedSchedule
import json
from django.views.decorators.csrf import csrf_exempt
from logger import get_logger
from .utils import get_list_run_date, get_next_run
from django.utils import timezone
from datetime import datetime
from django.db.models import Max
from batchbe.celery import app
from .models import JobSettings, TaskDetail
from celery.result import AsyncResult
from request_entities.schedule_task import SchedulerTaskResponse
import requests
import uuid

logger = get_logger()


class CeleryBeTask:
    def __init__(self, celery_task_name, run_date, next_run_date):
        self.celery_task_name = celery_task_name
        self.run_date = run_date
        self.next_run_date = next_run_date


@csrf_exempt
def delete_task(request, task_id):
    if request.method == 'DELETE':
        task = PeriodicTask.objects.get(id=task_id)
        task.delete()
        return JsonResponse({'status': 'success', 'message': 'Task deleted successfully.'})

    return JsonResponse({'status': 'failure', 'message': 'Invalid request method.'})


@csrf_exempt
def rrule_schedule_task(request):
    if request.method == 'POST':
        try:
            required_fields = ['job_id', 'max_run_duration', 'max_run', 'max_failure', 'is_enable', 'auto_drop',
                               'restart_on_failure', 'restartable', 'priority', 'job_type', 'job_action',
                               'repeat_interval', 'start_date', 'end_date', 'max_run', 'queue_name', 'user_name',
                               'retry_delay']
            data = get_request_data(request, required_fields)
            logger.info(f'Received request to create interval task with body {json.loads(request.body)}')
            job_id = data.get('job_id')
            max_run_duration = data.get('max_run_duration')
            max_run = data.get('max_run')
            max_failures = data.get('max_failure')
            enable = data.get('is_enable')
            auto_drop = data.get('auto_drop')
            restart_on_fail = data.get('restart_on_failure')
            restartable = data.get('restartable')
            priority = data.get('priority')

            job_type = data.get('job_type')
            job_action = data.get('job_action')
            job_body = data.get('job_body')
            rrule_str = data['repeat_interval']
            start_date = timezone.make_aware(datetime.fromisoformat(data['start_date']))
            end_date = timezone.make_aware(datetime.fromisoformat(data['end_date']))
            run_count = data['max_run']
            queue_name = data.get('queue_name')
            run_account = data.get('user_name')
            retry_delay = data.get('retry_delay')

            # Ensure task_func and task_name, queue_name are provided
            if not job_type or not job_id or not queue_name:
                return JsonResponse(
                    {'status': 'failure', 'message': 'Job function and job name and queue name are required.'})

            function_name = f'celerytasks.tasks.{job_type.lower()}'

            try:
                job_settings = JobSettings.objects.create(job_id=job_id, queue_name=queue_name,
                                                          function_name=function_name,
                                                          start_date=start_date,
                                                          end_date=end_date, repeat_interval=rrule_str,
                                                          max_run_duration=max_run_duration,
                                                          max_run=max_run,
                                                          max_failure=max_failures, priority=priority,
                                                          is_enable=enable, auto_drop=auto_drop,
                                                          restart_on_failure=restart_on_fail,
                                                          restartable=restartable, job_type=job_type,
                                                          job_action=job_action,
                                                          run_account=run_account,
                                                          retry_delay=retry_delay, job_body=job_body)
                logger.info(f'Save job_settings: {job_settings} to database successfully')
            except Exception as e:
                logger.error(f'Cannot save job_settings to database error: {e}')
                return JsonResponse({'status': 'error', 'message': f'Save job_settings to database with exception {e}'},
                                    status=405)

            # Calculate the next run times
            next_runs = get_list_run_date(rrule_str, run_count, start_date, end_date)

            # Create a ClockedSchedule for each run time
            clocked_schedules = []
            celery_tasks = []
            for i, next_run in enumerate(next_runs):
                clocked_schedule = ClockedSchedule.objects.create(clocked_time=next_run)
                clocked_schedules.append(clocked_schedule)

                # Determine the next_run_date (next element in the list or None if it's the last one)
                next_run_date = next_runs[i + 1] if i + 1 < len(next_runs) else None

                # Create CeleryBeTask object with the current run time and next_run_date
                celery_be_task = CeleryBeTask(
                    celery_task_name=str(uuid.uuid4()),
                    run_date=next_run,
                    next_run_date=str(next_run_date)
                )
                celery_tasks.append(celery_be_task)

            # Create PeriodicTask for each ClockedSchedule
            # TODO: Refactor
            tasks = []
            for i, clocked_schedule in enumerate(clocked_schedules):
                task_name = celery_tasks[i].celery_task_name

                try:
                    task = PeriodicTask.objects.get_or_create(
                        clocked=clocked_schedule,
                        name=task_name,
                        task=function_name,
                        defaults={'one_off': True},
                        description=job_id,
                        queue=queue_name,
                        exchange=queue_name,
                        enabled=True,
                        priority=priority,
                        args=json.dumps([job_action, task_name, job_id, run_account, celery_tasks[i].next_run_date]),
                    )
                    tasks.append(task)
                    logger.info(f'Save PeriodicTask: {task} to database successfully')

                except Exception as e:
                    logger.error(f'Cannot save PeriodicTask to database error {e}')
                    return JsonResponse(
                        {'status': 'error', 'message': f'Cannot save PeriodicTask to database exception {e}'},
                        status=405)
                try:
                    task_detail = TaskDetail.objects.get_or_create(job=job_settings, task_name=task_name,
                                                                   run_date=clocked_schedule.clocked_time)
                    logger.info(f'Save TaskDetail: {task_detail} to database successfully')
                except Exception as e:
                    logger.error(f'Cannot save TaskDetail to database error {e}')
                    return JsonResponse(
                        {'status': 'error', 'message': f'Cannot save TaskDetail to database exception {e}'},
                        status=405)

            task_responses = [
                SchedulerTaskResponse(task.celery_task_name, task.run_date)
                for task in celery_tasks]
            task_dicts = [task_response.to_dict() for task_response in task_responses]
            logger.info(f'Created interval task with job_id {job_id} and tasks {task_dicts}')
            return JsonResponse({'status': 'success', 'next_run_date': next_runs[0], 'tasks': task_dicts})
        except KeyError as e:
            logger.error(f'Missing parameter: {str(e)}')
            return JsonResponse({'status': 'error', 'message': f'Missing parameter: {str(e)}'}, status=400)
        except Exception as e:
            logger.error(f'Error in creating interval task: {e}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def manually_run(request):
    if request.method == 'POST':
        try:
            required_fields = ['job_id', 'job_type', 'job_action', 'queue_name', 'user_name']
            data = get_request_data(request, required_fields)
            job_id = data.get('job_id')
            job_type = data.get('job_type')
            job_action = data.get('job_action')
            queue_name = data.get('queue_name')
            run_account = data.get('user_name')

            if not job_type or not queue_name or not job_action or not job_id:
                return JsonResponse(
                    {'status': 'failure', 'message': 'Job type, job action, job_id and queue_name are required.'})

            job_settings = JobSettings.objects.filter(job_id=job_id).first()

            clocked_schedule = ClockedSchedule.objects.create(clocked_time=datetime.now())

            # Create PeriodicTask for each ClockedSchedule
            task_name = str(uuid.uuid4())
            task, created = PeriodicTask.objects.get_or_create(
                clocked=clocked_schedule,
                name=task_name,
                task=f'celerytasks.tasks.{job_type.lower()}',
                defaults={'one_off': True},
                description=job_id,
                queue=queue_name,
                exchange=queue_name,
                args=json.dumps([job_action, task_name, job_id, run_account]),
            )

            if not created:
                task.clocked = clocked_schedule
                task.enabled = True
                task.queue = queue_name
                task.save()

            task_detail, created = TaskDetail.objects.get_or_create(job=job_settings, task_name=task_name,
                                                                    run_date=clocked_schedule.clocked_time)
            if not created:
                task_detail.save()

            return JsonResponse(
                {'status': 'success', 'message': f'Job {job_id} assigned to worker with queue {queue_name}.'})

        except KeyError as e:
            return JsonResponse({'status': 'error', 'message': f'Missing parameter: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def force_terminate_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        job_id = data.get('job_id')
        latest_task = get_latest_running_task(job_id)
        if latest_task is None:
            return JsonResponse({'status': 'error', 'message': f'No running job found for job_id {job_id}'}, status=404)

        task_id = latest_task.task_id
        result = AsyncResult(task_id, app=app)
        result.revoke(terminate=True, signal='SIGKILL')
        latest_task.save_status(TaskDetail.STATUS_CANCELLED)
        return JsonResponse(
            {'status': 'success', 'message': f'Job {job_id} force terminated with task_id {task_id}.'})
    return JsonResponse({'status': 'failure', 'message': 'Invalid request method.'})


# Mapping dictionary: job_settings_field -> periodic_task_field
FIELD_MAPPING = {
    'queue_name': 'queue',
    'is_enable': 'enabled',
    # Add more mappings as required
}

# Fields that only exist in JobSettings
JOB_SETTINGS_ONLY_FIELDS = {'start_date', 'end_date', 'repeat_interval', 'max_run_duration',
                            'max_run', 'max_failure', 'auto_drop', 'restart_on_failure',
                            'restartable', 'priority', 'job_action',
                            'queue_name', 'user_name', 'retry_delay'}


@csrf_exempt
def update_job(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f'Received request to update job with body {data}')
            # Get job_id from query parameters
            job_id = data.get('job_id')
            if not job_id:
                return JsonResponse({'status': 'error', 'message': 'job_id parameter is required'}, status=400)

            job_settings = JobSettings.objects.filter(job_id=job_id).first()
            if not job_settings:
                return JsonResponse({'status': 'error', 'message': f'Cannot find JobSettings with job_id={job_id}'},
                                    status=400)

            data = json.loads(request.body)

            # Update TaskDetail objects
            tasks = PeriodicTask.objects.filter(description=job_id).order_by('id')
            done_tasks = list(filter(lambda t: t.enabled is False, tasks))
            last_max_run = len(tasks)
            if not tasks.exists():
                return JsonResponse({'status': 'error', 'message': f'No enabled tasks found for job_id {job_id}'},
                                    status=404)

            max_run = data.get('max_run')
            if max_run is not None:
                if len(done_tasks) >= max_run:
                    return JsonResponse({'status': 'error',
                                         'message': f'Task has been run {len(done_tasks)} times, Cannot update to minor '
                                                    f'max_run'},
                                        status=400)

                if last_max_run > max_run:
                    # Hard delete tasks to reduce the number to max_run
                    tasks_to_delete = tasks[max_run:]
                    logger.info(f'Deleting tasks: {tasks_to_delete}')
                    PeriodicTask.objects.filter(name__in=[task.name for task in tasks_to_delete]).all().delete()

                if last_max_run < max_run:
                    not_done_tasks = list(filter(lambda t: t.enabled is True, tasks))
                    logger.info(f'Deleting not done tasks: {not_done_tasks}')
                    PeriodicTask.objects.filter(name__in=[task.name for task in not_done_tasks]).all().delete()

                    logger.info(f'Creating new tasks for job_id {job_id}')
                    rrule_str = data.get('repeat_interval', job_settings.repeat_interval)
                    run_count = data.get('max_run') - len(done_tasks)
                    start_date = data.get('start_date', job_settings.start_date)
                    end_date = data.get('end_date', job_settings.end_date)
                    # Calculate the next run times
                    next_runs = get_list_run_date(rrule_str, run_count, start_date, end_date)
                    # Create a ClockedSchedule for each run time
                    clocked_schedules = []
                    celery_tasks = []
                    for next_run in next_runs:
                        clocked_schedule = ClockedSchedule.objects.create(clocked_time=next_run)
                        clocked_schedules.append(clocked_schedule)
                        celery_be_task = CeleryBeTask(celery_task_name=str(uuid.uuid4()), run_date=next_run)
                        celery_tasks.append(celery_be_task)

                    # Create PeriodicTask for each ClockedSchedule
                    # TODO: Refactor
                    for i, clocked_schedule in enumerate(clocked_schedules):
                        task_name = celery_tasks[i].celery_task_name

                        task, created = PeriodicTask.objects.get_or_create(
                            clocked=clocked_schedule,
                            name=task_name,
                            task=job_settings.unction_name,
                            defaults={'one_off': True},
                            description=job_id,
                            queue=job_settings.queue_name,
                            exchange=job_settings.queue_name,
                            priority=job_settings.priority,
                            args=json.dumps([job_settings.job_action, task_name, job_id, job_settings.run_account]),
                        )
                        if not created:
                            task.clocked = clocked_schedule
                            task.enabled = True
                            task.queue = job_settings.queue_name
                            task.save()
            else:
                for task in tasks:
                    for key, value in data.items():
                        if key in FIELD_MAPPING:
                            task_key = FIELD_MAPPING[key]
                            if hasattr(task, task_key):
                                setattr(task, task_key, value)
                    task.save()

            # Update JobSettings object
            job_settings = JobSettings.objects.filter(job_id=job_id).first()
            if job_settings is None:
                return JsonResponse({'status': 'error', 'message': f'No job found for job_id {job_id}'}, status=404)

            for key, value in data.items():
                if key in FIELD_MAPPING:
                    if hasattr(job_settings, key):
                        setattr(job_settings, key, value)
                elif key in JOB_SETTINGS_ONLY_FIELDS:
                    setattr(job_settings, key, value)

            job_settings.save()

            return JsonResponse(
                {'status': 'success', 'message': f'Job {job_id} and related tasks updated successfully.'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def get_latest_running_task(job_id):
    job_settings = JobSettings.objects.filter(job_id=job_id).first()
    latest_job = TaskDetail.objects.filter(job=job_settings, status=TaskDetail.STATUS_RUNNING).order_by(
        '-run_date').first()
    return latest_job


def get_request_data(request, required_fields):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format")
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    return {field: data[field] for field in required_fields}


def health_check(request):
    return JsonResponse({"status": "ok"})


def convert_task_detail_to_log_data(task_detail, job_settings, result, operation):
    try:
        return {
            "job_id": task_detail.job.job_id,
            "operation": operation,
            "status": task_detail.status,
            "user_name": task_detail.run_account,
            "error_no": job_settings.failure_count,
            "req_start_date": task_detail.created_at.isoformat(),
            "actual_start_date": task_detail.run_date.isoformat(),
            "run_duration": str(task_detail.run_duration) if task_detail.run_duration else None,
            "additional_info": "abc",
            "errors": str(result) if job_settings.failure_count > 0 else None,
            "output": str(result),
            "run_count": job_settings.run_count,
            "failure_count": job_settings.failure_count,
            "retry_count": job_settings.retry_count,
        }
    except Exception as e:
        logger.error(f'Error in converting task detail to log data: {e}')
        return None