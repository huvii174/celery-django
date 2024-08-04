import json
from datetime import datetime


class SchedulerJobs:
    def __init__(self, celery_task_name, operation, status, user_name, error_no, req_start_date, actual_start_date,
                 next_run_date, run_duration, additional_info, errors, output):
        self.celery_task_name = celery_task_name
        self.operation = operation
        self.status = status
        self.user_name = user_name
        self.error_no = error_no
        self.req_start_date = self.convert_date(req_start_date)
        self.actual_start_date = self.convert_date(actual_start_date)
        self.next_run_date = self.convert_date(next_run_date)
        self.run_duration = run_duration
        self.additional_info = additional_info
        self.errors = errors
        self.output = output

    def __str__(self):
        return f'Celery Task Name: {self.celery_task_name}, Operation: {self.operation}, Job Status: {self.status}'

    def __repr__(self):
        return f'Celery Task Name: {self.celery_task_name}, Operation: {self.operation}, Job Status: {self.status}'

    def to_dict(self):
        return {
            "celery_task_name": self.celery_task_name,
            "operation": self.operation,
            "status": self.status,
            "user_name": self.user_name,
            "error_no": self.error_no,
            "req_start_date": self.req_start_date if self.req_start_date else None,
            "actual_start_date": self.actual_start_date if self.actual_start_date else None,
            "next_run_date": self.next_run_date if self.next_run_date else None,
            "run_duration": self.run_duration,
            "additional_info": self.additional_info,
            "errors": self.errors,
            "output": self.output
        }

    @staticmethod
    def convert_date(date_str):
        if date_str:
            return datetime.strftime(date_str, format="%Y-%m-%d %H:%M:%S")
        return None