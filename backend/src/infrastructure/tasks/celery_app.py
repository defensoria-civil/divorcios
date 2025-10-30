import os
from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app = Celery("def_civil", broker=redis_url, backend=redis_url, include=["infrastructure.tasks.jobs"])

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Argentina/Mendoza",
    enable_utc=True,
)
