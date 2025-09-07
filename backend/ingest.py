# backend/ingest.py
"""
Reusable ingestion functions. These mirror the logic you already have in main endpoints,
but are packaged here so workers/scheduler can call them.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from fetch_usgs import fetch_usgs_quakes
from fetch_rss import fetch_rss_items
from models import Item

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
    try:
        items = fetch_rss_items()
        inserted = 0
        
        if not items:
            logger.warning("No items found in RSS feed")
            return 0
            
        logger.info(f"Processing {len(items)} items from RSS feed")
        
        for r in items:
            try:
                ext_id = r.get("id") or r.get("link")
                if not ext_id:
                    logger.warning("Skipping item with no ID or link")
                    continue
                    
                # Check if item already exists
                exists = db.query(Item).filter(
                    (Item.ext_id == ext_id) & 
                    (Item.source == "GDACS")
                ).first()
                
                if exists:
                    logger.debug(f"Skipping duplicate item: {ext_id}")
                    continue
                
                # Prepare item data
                title = r.get("title", "").strip()
                description = r.get("summary", "").strip()
                text = f"{title} {description}".strip()
                
                # Create new item
                item = Item(
                    ext_id=ext_id,
                    source="GDACS",
                    source_handle=r.get("source_feed", "GDACS"),
                    text=text,
                    place=title,
                    lat=r.get("lat"),
                    lon=r.get("lon"),
                    disaster_type=r.get("disaster_type", "unknown"),
                    raw_json=r.get("raw", {})
                )
                
                db.add(item)
                inserted += 1
                logger.debug(f"Added new item: {ext_id} - {title}")
                
            except Exception as e:
                logger.error(f"Error processing RSS item {r.get('id', 'unknown')}: {str(e)}", exc_info=True)
                continue
        
        db.commit()
        logger.info(f"GDACS RSS ingest complete. Fetched: {len(items)}, Inserted: {inserted}")
        return inserted
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in RSS ingestion: {str(e)}", exc_info=True)
        return 0
