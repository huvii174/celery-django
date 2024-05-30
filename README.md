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

Update the environment variables in docker-compose.yml with your PostgreSQL credentials:

```yaml
environment:
  - DATABASE_URL=postgres://your_db_user:your_db_password@host.docker.internal:5432/your_db_name
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
backports.zoneinfo
```

## Configuration
#### 1.Update settings.py:

Ensure that your settings.py includes configurations for Celery:

```python
import os
from pathlib import Path
import dj_database_url
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'django_celery_results',
    'celerytasks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'batchbe.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'batchbe.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'django-db')
```

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
