from celery import Task


class RepeatTask(Task):
    def before_start(self, task_id, args, kwargs):
        print(f'-----------task {task_id}')
