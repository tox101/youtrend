import os
from celery import Celery

# Redis broker configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"

app = Celery(
    "yt_intelligence",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        "scheduler.celery_tasks"
    ]
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Beat schedule: fires the full pipeline every 5 minutes
    beat_schedule={
        "crawl-rank-pipeline-every-5min": {
            "task": "scheduler.celery_tasks.run_full_pipeline",
            "schedule": 300.0,  # 5 minutes
        },
    },
)
