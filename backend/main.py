import os, uuid, json
from typing import Optional, List
from fastapi import FastAPI, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from loguru import logger

from db import Base, engine, get_db
from models import Item
from fetch_usgs import fetch_usgs_quakes
from services.nlp_service import nlp_service
from services.geocoding_service import geocoding_service
from services.credibility_service import credibility_service

# --- setup & CORS ---
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CrisisConnect API", version="0.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# static uploads
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

def process_item_with_nlp_geocoding(item: Item, text: str) -> Item:
    """Process an item with NLP and geocoding services"""
    if not text:
        return item
    
    # Process text with NLP
    nlp_result = nlp_service.process_text(text)
    
    # Update item with NLP results
    item.language = nlp_result.get('language')
    item.disaster_type = nlp_result.get('disaster_type')
    
    # If we don't have coordinates, try to geocode from extracted locations
    if not item.lat or not item.lon:
        locations = nlp_result.get('locations', [])
        if locations:
            # Extract location texts
            location_texts = [loc.get('text', '') for loc in locations if loc.get('text')]
            
            # Add the place field if available
            if item.place:
                location_texts.insert(0, item.place)
            
            # Process locations with geocoding
            geocoding_result = geocoding_service.process_locations(location_texts)
            
            if geocoding_result:
                item.lat = geocoding_result.get('lat')
                item.lon = geocoding_result.get('lon')
                # Store geometry as WKT string for PostGIS
                geom_wkt = geocoding_result.get('geometry')
                if geom_wkt:
                    # We'll update the geom field via raw SQL in the database
                    pass
                
                # Update place with formatted address if we got one
                if not item.place and geocoding_result.get('formatted_address'):
                    item.place = geocoding_result.get('formatted_address')
    
    return item

def process_item_with_credibility(item: Item, db: Session) -> Item:
    """Process an item with credibility scoring"""
    return credibility_service.process_item_credibility(item, db)

@app.on_event("startup")
def startup_event():
    logger.info("🚀 CrisisConnect backend started")

# --- health ---
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "CrisisConnect API is running"}

@app.get("/status")
def status_check():
    return {"status": "ok", "message": "CrisisConnect API is running"}

@app.get("/")
def root():
    return {
        "message": "CrisisConnect API", 
        "version": "0.4",
        "docs": "/docs",
        "health": "/health"
    }

# --- pullers: USGS ---
@app.get("/ingest/usgs")
def ingest_usgs(db: Session = Depends(get_db)):
    try:
        data = fetch_usgs_quakes()
        new_count = 0
        events = []
        
        for e in data:
            ext_id = e.get("id")
            if not ext_id:
                continue
                
            # Check if this earthquake already exists
            exists = db.query(Item).filter(Item.ext_id == ext_id, Item.source == "USGS").first()
            lon, lat, depth = (e.get("coordinates") or [None, None, None]) + [None] * (3 - len(e.get("coordinates") or []))
            
            event_data = {
                "id": ext_id,
                "place": e.get("place"),
                "magnitude": e.get("magnitude"),
                "time_utc": e.get("time_utc"),
                "url": e.get("url"),
                "coordinates": [lon, lat, depth],
                "raw": e.get("raw", {})
            }
            events.append(event_data)
            
            if not exists and lat is not None and lon is not None:
                # Only add to database if it's new and has coordinates
                item = Item(
                    ext_id=ext_id,
                    source="USGS",
                    source_handle="USGS",
                    text=e.get("place"),
                    magnitude=e.get("magnitude"),
                    place=e.get("place"),
                    lat=lat,
                    lon=lon,
                    raw_json=event_data,
                )
                
                # Process with NLP and geocoding
                item = process_item_with_nlp_geocoding(item, e.get("place", ""))
                
                # Process with credibility scoring
                item = process_item_with_credibility(item, db)
                
                db.add(item)
                new_count += 1
                
        db.commit()
        return {
            "inserted": new_count,
            "fetched": len(events),
            "events": events  # Return the events for the frontend
        }
    except Exception as e:
        logger.error(f"Error in USGS ingestion: {str(e)}")
        return {"error": str(e), "inserted": 0, "fetched": 0, "events": []}

# --- stubs: Reddit & X (use seeds if no API keys yet) ---
def _load_seed(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Seed load failed: {e}")
        return []

@app.get("/ingest/seed/reddit")
def ingest_seed_reddit(db: Session = Depends(get_db)):
    seed = _load_seed(os.path.join(os.getcwd(), "seeds", "reddit_seed.json"))
    new = 0
    for s in seed:
        ext_id = s.get("id")
        if not ext_id:
            continue
        exists = db.query(Item).filter(Item.ext_id == ext_id, Item.source == "REDDIT").first()
        if exists:
            continue
        item = Item(
            ext_id=ext_id,
            source="REDDIT",
            source_handle=s.get("subreddit"),
            text=(s.get("title") or "") + " - " + (s.get("text") or ""),
            place=None,
            lat=s.get("lat"),
            lon=s.get("lon"),
            raw_json=s
        )
        
        # Process with NLP and geocoding
        item = process_item_with_nlp_geocoding(item, item.text)
        
        # Process with credibility scoring
        item = process_item_with_credibility(item, db)
        
        db.add(item)
        new += 1
    db.commit()
    return {"inserted": new, "fetched": len(seed)}

@app.get("/ingest/seed/x")
def ingest_seed_x(db: Session = Depends(get_db)):
    seed = _load_seed(os.path.join(os.getcwd(), "seeds", "x_seed.json"))
    new = 0
    for s in seed:
        ext_id = s.get("id")
        if not ext_id:
            continue
        exists = db.query(Item).filter(Item.ext_id == ext_id, Item.source == "X").first()
        if exists:
            continue
        item = Item(
            ext_id=ext_id,
            source="X",
            source_handle=s.get("handle"),
            text=s.get("text"),
            place=None,
            lat=s.get("lat"),
            lon=s.get("lon"),
            raw_json=s
        )
        
        # Process with NLP and geocoding
        item = process_item_with_nlp_geocoding(item, item.text)
        
        # Process with credibility scoring
        item = process_item_with_credibility(item, db)
        
        db.add(item)
        new += 1
    db.commit()
    return {"inserted": new, "fetched": len(seed)}

# --- citizen web form ingest (multipart) ---
@app.post("/api/ingest")
async def ingest_citizen(
    text: str = Form(...),
    lat: Optional[float] = Form(None),
    lon: Optional[float] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    media_url = None
    if file:
        # naive file validation (content-type startswith image/)
        if not (file.content_type or "").startswith("image/"):
            return {"ok": False, "error": "Only image uploads supported for now."}
        ext = os.path.splitext(file.filename or "")[1] or ".jpg"
        fname = f"{uuid.uuid4().hex}{ext}"
        fpath = os.path.join(UPLOAD_DIR, fname)
        with open(fpath, "wb") as out:
            out.write(await file.read())
        media_url = f"/uploads/{fname}"

    item = Item(
        ext_id=str(uuid.uuid4()),
        source="CITIZEN",
        source_handle="web_form",
        text=text[:4000],
        lat=lat,
        lon=lon,
        media_url=media_url,
        raw_json={"text": text, "lat": lat, "lon": lon, "media_url": media_url}
    )
    
    # Process with NLP and geocoding
    item = process_item_with_nlp_geocoding(item, text)
    
    # Process with credibility scoring
    item = process_item_with_credibility(item, db)
    
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"ok": True, "id": item.id, "media_url": media_url}

# --- list items for map ---
@app.get("/api/items")
def list_items(
    min_credibility: Optional[float] = None,
    needs_review: Optional[str] = None,
    suspected_rumor: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Item)
    
    # Apply filters
    if min_credibility is not None:
        query = query.filter(Item.score_credibility >= min_credibility)
    
    if needs_review is not None:
        query = query.filter(Item.needs_review == needs_review)
    
    if suspected_rumor is not None:
        query = query.filter(Item.suspected_rumor == suspected_rumor)
    
    rows = query.order_by(Item.created_at.desc()).limit(500).all()
    
    def to_dict(r: Item):
        return {
            "id": r.id,
            "ext_id": r.ext_id,
            "source": r.source,
            "source_handle": r.source_handle,
            "text": r.text,
            "place": r.place,
            "magnitude": r.magnitude,
            "lat": r.lat,
            "lon": r.lon,
            "media_url": r.media_url,
            "language": r.language,
            "disaster_type": r.disaster_type,
            "score_credibility": r.score_credibility,
            "needs_review": r.needs_review,
            "suspected_rumor": r.suspected_rumor,
            "credibility_signals": r.credibility_signals,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
    return {"count": len(rows), "items": [to_dict(r) for r in rows]}

# --- process existing items with NLP and geocoding ---
@app.post("/api/process-nlp-geocoding")
def process_existing_items(db: Session = Depends(get_db)):
    """Process existing items that don't have NLP or geocoding data"""
    try:
        # Find items without language or disaster_type
        items_to_process = db.query(Item).filter(
            (Item.language.is_(None)) | (Item.disaster_type.is_(None))
        ).limit(100).all()  # Process in batches
        
        processed_count = 0
        for item in items_to_process:
            if item.text:
                # Process with NLP and geocoding
                processed_item = process_item_with_nlp_geocoding(item, item.text)
                
                # Update the item in the database
                item.language = processed_item.language
                item.disaster_type = processed_item.disaster_type
                if processed_item.lat and not item.lat:
                    item.lat = processed_item.lat
                if processed_item.lon and not item.lon:
                    item.lon = processed_item.lon
                if processed_item.place and not item.place:
                    item.place = processed_item.place
                
                processed_count += 1
        
        db.commit()
        
        return {
            "status": "ok",
            "processed_count": processed_count,
            "total_items": db.query(Item).count()
        }
    except Exception as e:
        logger.error(f"Error processing items: {str(e)}")
        return {"error": str(e), "processed_count": 0}

# --- process existing items with credibility scoring ---
@app.post("/api/process-credibility")
def process_existing_items_credibility(db: Session = Depends(get_db)):
    """Process existing items that don't have credibility scores"""
    try:
        # Find items without credibility scores
        items_to_process = db.query(Item).filter(
            Item.score_credibility.is_(None)
        ).limit(100).all()  # Process in batches
        
        processed_count = 0
        for item in items_to_process:
            # Process with credibility scoring
            processed_item = process_item_with_credibility(item, db)
            
            # Update the item in the database
            item.score_credibility = processed_item.score_credibility
            item.needs_review = processed_item.needs_review
            item.suspected_rumor = processed_item.suspected_rumor
            item.credibility_signals = processed_item.credibility_signals
            
            processed_count += 1
        
        db.commit()
        
        return {
            "status": "ok",
            "processed_count": processed_count,
            "total_items": db.query(Item).count()
        }
    except Exception as e:
        logger.error(f"Error processing credibility: {str(e)}")
        return {"error": str(e), "processed_count": 0}

# --- credibility statistics ---
@app.get("/api/credibility-stats")
def credibility_stats(db: Session = Depends(get_db)):
    """Get credibility statistics for all items"""
    try:
        total_items = db.query(Item).count()
        items_with_credibility = db.query(Item).filter(Item.score_credibility.isnot(None)).count()
        
        # Get credibility score distribution
        credibility_scores = db.query(Item.score_credibility).filter(
            Item.score_credibility.isnot(None)
        ).all()
        
        scores = [score[0] for score in credibility_scores]
        
        # Calculate statistics
        avg_credibility = sum(scores) / len(scores) if scores else 0
        min_credibility = min(scores) if scores else 0
        max_credibility = max(scores) if scores else 0
        
        # Count by credibility ranges
        high_credibility = db.query(Item).filter(Item.score_credibility >= 0.7).count()
        medium_credibility = db.query(Item).filter(
            Item.score_credibility >= 0.4, 
            Item.score_credibility < 0.7
        ).count()
        low_credibility = db.query(Item).filter(Item.score_credibility < 0.4).count()
        
        # Count flags
        needs_review_count = db.query(Item).filter(Item.needs_review == 'true').count()
        suspected_rumor_count = db.query(Item).filter(Item.suspected_rumor == 'true').count()
        
        return {
            "total_items": total_items,
            "items_with_credibility": items_with_credibility,
            "credibility_stats": {
                "average": round(avg_credibility, 3),
                "minimum": round(min_credibility, 3),
                "maximum": round(max_credibility, 3)
            },
            "credibility_distribution": {
                "high_credibility": high_credibility,
                "medium_credibility": medium_credibility,
                "low_credibility": low_credibility
            },
            "flags": {
                "needs_review": needs_review_count,
                "suspected_rumor": suspected_rumor_count
            }
        }
    except Exception as e:
        logger.error(f"Error getting credibility stats: {str(e)}")
        return {"error": str(e)}

# --- convenience loader: try to reach 50+ items ---
@app.get("/ingest/sample")
def load_sample(db: Session = Depends(get_db)):
    # Load USGS data
    usgs = ingest_usgs(db)
    return {"status": "ok", "total_items": db.query(Item).count()}
