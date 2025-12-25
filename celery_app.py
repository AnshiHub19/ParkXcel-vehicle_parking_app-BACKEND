from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
import os

celery_app = Celery(
    "MAD2",
    broker="redis://localhost:6380/0",
    backend="redis://localhost:6380/0"
)

os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')
celery_app.loader.import_default_modules()
import tasks  # Register tasks

# TESTING SCHEDULE - 10s Daily, 20s Monthly
celery_app.conf.beat_schedule = {
    "daily-parking-reminder": {
        "task": "tasks.sendparkingreminders",
        "schedule": timedelta(seconds=10), 
    },
    "monthly-parking-report": {
        "task": "tasks.send_monthly_parking_report",
        "schedule": timedelta(seconds=20),  # HAR 20 SECOND!
    },
}

celery_app.conf.timezone = 'Asia/Kolkata'
