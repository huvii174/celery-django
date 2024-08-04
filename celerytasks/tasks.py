from celery import shared_task
from datetime import date
from .custom_task import RepeatTask
from logger import get_logger
import subprocess
import shlex
import requests
import re

logger = get_logger()


@shared_task(bind=True, base=RepeatTask)
def rest_api(self, job_action, job_name, job_id, run_account, next_run_date):
    """
        Calls a REST API using an input string formatted with the HTTP method, URL, and headers.

        Args:
            request_string (str): The full HTTP request string including method, URL, headers.

        Returns:
            response: The response object from the API call.
        """
    logger.info(
        f'Start execute schedule task id: {job_id} with type REST_API with action = {job_action}, user :{run_account}')
    try:
        # Split the input into lines
        lines = job_action.splitlines()

        # Extract method and URL from the first line
        method_line = lines[0]
        method, url, _ = re.split(r'\s+', method_line, maxsplit=2)

        # Extract headers
        headers = {}
        for line in lines[1:]:
            if line.strip() == "":
                continue
            header_name, header_value = line.split(':', 1)
            headers[header_name.strip()] = header_value.strip()

        # Make the API call based on the method
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, header=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        logger.info(
            f'Successfully execute schedule task id: {job_id} with type REST_API with response = {response}')
        return response
    except Exception as e:
        logger.error(f'Fail to execute schedule task id: {job_id} with error :{e}')
        return None


@shared_task(bind=True, base=RepeatTask)
def executable(self, job_action, job_name, job_id, run_account, next_run_date):
    """
        Calls a Bash shell script with the specified command line.

        Args:
            command_line (str): The command line string containing the script path and arguments.

        Returns:
            output (str): The standard output from the script.
            error (str): The standard error output from the script, if any.
            returncode (int): The return code from the script execution.
        """
    logger.info(
        f'Start execute schedule task id: {job_id} with type EXECUTABLE with action = {job_action}, user :{run_account}')
    try:
        # Split the command line into the script path and arguments
        command = shlex.split(job_action)
        # Execute the script
        result = subprocess.run(command, capture_output=True, text=True, shell=False)
        logger.info(
            f'Successfully execute schedule task id: {job_id} with type EXECUTABLE with response = {result}')
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        logger.error(f'Fail to execute schedule task id: {job_id} with error :{e}')
        return None, str(e), -1
