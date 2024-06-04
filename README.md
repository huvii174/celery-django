# Batchbe Django Celery App

This project is a Django application integrated with Celery for background task processing. 

It uses Redis as the message broker and PostgreSQL as the result backend. The application supports dynamic task scheduling with interval and cron-like schedules, and it includes endpoints for CRUD operations on these tasks. Docker is used to containerize the application.

## Table of Contents
- Requirements
- Installation
- Configuration
- Running the Application
- API Endpoints
- Usage
- Monitoring
- References

## Requirements
- Docker
- Docker Compose
- PostgreSQL (running on host machine)
- Python 3.8

## Installation
#### 1. Set up PostgreSQL on your host machine:

Ensure that PostgreSQL is running and accessible from your host machine.

Configure environment variables:

Create and update .env file following env-sample
```dotenv
POSTGRES_HOST="host.docker.internal"
POSTGRES_USERNAME="username"
POSTGRES_PASSWORD="password"
POSTGRES_DB="batch-be"
```

#### 2.Install dependencies:

Ensure that requirements.txt includes all necessary dependencies:

```plaintext
Django>=3.0,<4.0
celery
redis
psycopg2-binary
django-celery-results
django-celery-beat
dj-database-url
flower
python-dotenv
backports.zoneinfo
```

## Configuration
#### 1.Update settings.py:

Ensure that your settings.py includes configurations for Celery

## Running the Application
#### 1.Build and start the Docker containers:

```sh
docker-compose up --build
```

#### 2.Create a superuser for Django admin:

```sh
docker-compose run web python manage.py createsuperuser
```

## API Endpoints
### Create Interval Task
- URL: /celerytasks/create_interval_task/
- Method: POST
- Payload:
- 
```json
{
  "task_name": "celerytasks.tasks.add",
  "interval": 10,
  "args": [4, 4]
}
```

### Create Cron Task
- URL: /celerytasks/create_cron_task/
- Method: POST
- Payload:
- 
```json
{
  "task_name": "celerytasks.tasks.add",
  "minute": "0",
  "hour": "*/2",
  "day_of_week": "*",
  "day_of_month": "*",
  "month_of_year": "*",
  "args": [4, 4]
}
```

### Update Task
- URL: /celerytasks/update_task/<task_id>/
- Method: PUT
- Payload:
- 
```json
{
  "task_name": "celerytasks.tasks.add",
  "interval": 20,
  "args": [5, 5]
}
```

### Delete Task
- URL: /celerytasks/delete_task/<task_id>/
- Method: DELETE

### Create Task and Assign to specific Worker
- URL: /celerytasks/assign_task_to_worker/
- Method: POST
- Payload

```json
{
    "task_name": "celerytasks.tasks.add",
    "worker_id": "1",
    "args": [10, 23]
}
```

## Usage
#### 1.Create an interval task:

```sh
curl -X POST http://localhost:8000/celerytasks/create_interval_task/ -H "Content-Type: application/json" -d '{"task_name": "celerytasks.tasks.add", "interval": 10, "args": [4, 4]}'
```

#### 2.Create a cron task:

```sh
curl -X POST http://localhost:8000/celerytasks/create_cron_task/ -H "Content-Type: application/json" -d '{
    "task_name": "celerytasks.tasks.add",
    "minute": "0",
    "hour": "*/2",
    "day_of_week": "*",
    "day_of_month": "*",
    "month_of_year": "*",
    "args": [4, 4]
}'
```

#### 3.Update a task:

```sh
curl -X PUT http://localhost:8000/celerytasks/update_task/<task_id>/ -H "Content-Type: application/json" -d '{"task_name": "celerytasks.tasks.add", "interval": 20, "args": [5, 5]}'
```

#### 4.Delete a task:

```sh
curl -X DELETE http://localhost:8000/celerytasks/delete_task/<task_id>/ -H "Content-Type: application/json"
```

#### 5. Create Task and Assign to specific worker
```sh
curl -X POST http://localhost:8000/celerytasks/assign_task_to_worker/ \
-H "Content-Type: application/json" \
-d '{
    "task_name": "celerytasks.tasks.add",
    "worker_id": "1",
    "args": [10, 23]
}'
```

## Monitoring
Access the Flower monitoring dashboard:

Open your browser and navigate to http://localhost:5555.

## References

- [Django Documentation](https://docs.djangoproject.com/en/stable/)
- [Celery Documentation](https://docs.celeryproject.org/en/stable/)
- [Redis Documentation](https://redis.io/documentation)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django-Celery-Beat Documentation](https://django-celery-beat.readthedocs.io/en/latest/)
- [Django-Celery-Results Documentation](https://django-celery-results.readthedocs.io/en/latest/)
- [dj-database-url Documentation](https://pypi.org/project/dj-database-url/)
- [Flower Documentation](https://flower.readthedocs.io/en/latest/)
