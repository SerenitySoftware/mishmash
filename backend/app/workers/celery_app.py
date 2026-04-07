from celery import Celery

from app.config import settings

celery_app = Celery(
    "mishmash",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.runner_timeout_seconds + 60,
    task_soft_time_limit=settings.runner_timeout_seconds + 30,
    worker_max_tasks_per_child=50,
)

celery_app.autodiscover_tasks(["app.workers"])
