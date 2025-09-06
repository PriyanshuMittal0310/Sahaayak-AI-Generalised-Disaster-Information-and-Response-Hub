# backend/ingest.py
"""
Reusable ingestion functions. These mirror the logic you already have in main endpoints,
but are packaged here so workers/scheduler can call them.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from .fetch_usgs import fetch_usgs_quakes
from .fetch_rss import fetch_rss_items
from .models import Item

logger = logging.getLogger("ingest")
logger.setLevel(logging.INFO)


def ingest_usgs_to_db(db: Session) -> int:
    """
    Fetch USGS feed and insert new items into DB using the provided SQLAlchemy Session.
    Returns number of new rows inserted.
    """
    data = fetch_usgs_quakes()
    inserted = 0
    for e in data:
        ext_id = e.get("id")
        if not ext_id:
            continue
        exists = db.query(Item).filter(Item.ext_id == ext_id, Item.source == "USGS").first()
        if exists:
            continue
        lon, lat, *_ = e.get("coordinates") or [None, None]
        item = Item(
            ext_id=ext_id,
            source="USGS",
            source_handle="USGS",
            text=e.get("place"),
            magnitude=e.get("magnitude"),
            place=e.get("place"),
            lat=lat,
            lon=lon,
            raw_json=e.get("raw"),
        )
        db.add(item)
        inserted += 1

    db.commit()
    logger.info("USGS ingest: fetched %d inserted %d", len(data), inserted)
    return inserted


def ingest_rss_to_db(db: Session) -> int:
    """
    Fetch RSS feeds (GDACS by default) and insert new items into DB.
    Returns number of new rows inserted.
    """
    items = fetch_rss_items()
    inserted = 0
    for r in items:
        ext_id = r.get("id") or r.get("link")
        if not ext_id:
            continue
        exists = db.query(Item).filter(Item.ext_id == ext_id, Item.source == "GDACS").first()
        if exists:
            continue
        text = (r.get("title") or "") + (" | " + (r.get("summary") or "") if r.get("summary") else "")
        it = Item(
            ext_id=ext_id,
            source="GDACS",
            source_handle=r.get("source_feed"),
            text=text[:4000],
            place=None,
            lat=None,
            lon=None,
            raw_json=r.get("raw"),
        )
        db.add(it)
        inserted += 1

    db.commit()
    logger.info("RSS ingest: fetched %d inserted %d", len(items), inserted)
    return inserted
