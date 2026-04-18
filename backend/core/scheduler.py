"""APScheduler setup for background jobs."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone="Asia/Taipei")


def setup_scheduler():
    """Configure and return the scheduler instance. Jobs are added at startup in main.py."""
    return scheduler
