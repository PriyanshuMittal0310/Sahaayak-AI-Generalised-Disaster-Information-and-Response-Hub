# backend/tasks.py
"""
RQ-executable tasks. The worker will execute these functions.
They create their own DB session and call functions in ingest.py.
"""

import os
import logging
from db import SessionLocal
from ingest import ingest_usgs_to_db, ingest_rss_to_db

logger = logging.getLogger("tasks")
logger.setLevel(logging.INFO)


def ingest_usgs_task():
    """RQ task: ingest USGS feed into DB."""
    db = SessionLocal()
    try:
        n = ingest_usgs_to_db(db)
        logger.info("ingest_usgs_task inserted %d items", n)
        return {"inserted": n}
    except Exception as e:
        logger.exception("ingest_usgs_task failed: %s", e)
        raise
    finally:
        db.close()


def ingest_rss_task():
    """RQ task: ingest RSS feeds into DB."""
    db = SessionLocal()
    try:
        n = ingest_rss_to_db(db)
        logger.info("ingest_rss_task inserted %d items", n)
        return {"inserted": n}
    except Exception as e:
        logger.exception("ingest_rss_task failed: %s", e)
        raise
    finally:
        db.close()
