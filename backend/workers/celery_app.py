"""
Celery application setup.
This connects Celery to Redis (our message broker from Module 2) and
tells it where to find task definitions.
"""

from celery import Celery

from config.settings import settings

celery_app = Celery(
    "clipmind",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Automatically discover task functions defined in workers/tasks.py
celery_app.autodiscover_tasks(["workers"])
celery_app.conf.broker_connection_retry_on_startup = True
