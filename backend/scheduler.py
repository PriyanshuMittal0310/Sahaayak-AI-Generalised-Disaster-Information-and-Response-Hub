# backend/scheduler.py
"""
Register recurring ingestion jobs using rq-scheduler.
This script runs once (as a long-lived process) and ensures scheduled jobs exist.
"""

import os
import logging
from datetime import timedelta
from redis import Redis
from rq_scheduler import Scheduler

# If running inside docker-compose, host is 'redis', else use env REDIS_HOST
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

logger = logging.getLogger("scheduler")
logging.basicConfig(level=logging.INFO)

def main():
    r = Redis(host=REDIS_HOST, port=REDIS_PORT)
    sched = Scheduler(connection=r)

    # Interval seconds (can be customized via env)
    USGS_INTERVAL = int(os.getenv("USGS_INTERVAL_SECONDS", "120"))  # default 2 minutes
    RSS_INTERVAL = int(os.getenv("RSS_INTERVAL_SECONDS", "300"))    # default 5 minutes

    # job_id helps avoid duplicate scheduling
    usgs_job_id = "job:ingest_usgs"
    rss_job_id = "job:ingest_rss"

    # schedule USGS job (function path: tasks.ingest_usgs_task)
    # scheduled_time=None indicates immediate first run; interval in seconds repeats it
    try:
        # Remove existing job with same id if any (to update interval)
        existing = [j for j in sched.get_jobs() if j.id == usgs_job_id]
        if not existing:
            sched.schedule(
                scheduled_time=None,
                func='tasks.ingest_usgs_task',
                args=[],
                interval=USGS_INTERVAL,
                repeat=None,
                result_ttl=3600,
                id=usgs_job_id
            )
            logger.info("Scheduled USGS job every %s seconds", USGS_INTERVAL)
        else:
            logger.info("USGS job already scheduled")
    except Exception as e:
        logger.exception("Failed to schedule USGS job: %s", e)

    try:
        existing = [j for j in sched.get_jobs() if j.id == rss_job_id]
        if not existing:
            sched.schedule(
                scheduled_time=None,
                func='tasks.ingest_rss_task',
                args=[],
                interval=RSS_INTERVAL,
                repeat=None,
                result_ttl=3600,
                id=rss_job_id
            )
            logger.info("Scheduled RSS job every %s seconds", RSS_INTERVAL)
        else:
            logger.info("RSS job already scheduled")
    except Exception as e:
        logger.exception("Failed to schedule RSS job: %s", e)

    # scheduler process keeps running to maintain the scheduled jobs
    logger.info("Scheduler setup complete. Scheduler process will keep running.")
    # rq-scheduler keeps jobs in Redis; just block to keep the container alive
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopping")


if __name__ == "__main__":
    main()
