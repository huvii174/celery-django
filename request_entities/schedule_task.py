class SchedulerTaskResponse:
    def __init__(self, task_name, req_start_date):
        self.task_name = task_name
        self.req_start_date = req_start_date

    def to_dict(self):
        return {
            'celery_task_name': self.task_name,
            'req_start_date': self.req_start_date,
        }

    def __str__(self):
        return f'Celery Task Name: {self.task_name}, Request Start Date: {self.req_start_date}'