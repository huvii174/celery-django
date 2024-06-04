import os
from dotenv import load_dotenv

ENV = os.getenv("ENV")

if ENV is None:
    load_dotenv(f".env")
else:
    load_dotenv(f".env-{ENV}")


class POSTGRES:
    HOST = os.getenv('POSTGRES_HOST')
    USERNAME = os.getenv('POSTGRES_USERNAME')
    PASSWORD = os.getenv('POSTGRES_PASSWORD')
    DB = os.getenv('POSTGRES_DB')
    DATABASE_URL = f"postgresql://{USERNAME}:{PASSWORD}@{HOST}/{DB}"


class REDIS:
    HOST = os.getenv('REDIS_HOST')
    PORT = os.getenv('REDIS_PORT')
