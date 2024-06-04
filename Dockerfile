# Dockerfile

FROM python:3.8

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN pip install -r requirements.txt

# Copy project files
COPY . /code/

# Install custom lib
RUN pip install django-scheduler-0.1.tar.gz

# Copy and set permissions for the entrypoint script
COPY entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh