import os, uuid, json
from typing import Optional, List
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Request
from langdetect import detect, LangDetectException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from loguru import logger
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
load_dotenv()

from db import Base, engine, get_db
from models import Item
from fetch_usgs import fetch_usgs_quakes
from ingest import ingest_rss_to_db
from services.nlp_service import nlp_service
from services.geocoding_service import geocoding_service
from services.credibility_service import credibility_service

# Import API routers
from api.disaster_routes import router as disaster_router
from api.telegram_routes import router as telegram_router
from api.openai_routes import router as openai_router

# --- setup & CORS ---
app = FastAPI(
    title="Sahaayak AI API",
    description="Disaster Information and Response Hub API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    from db import init_db
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

# Configure CORS to allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Encoding",
        "Authorization",
        "Content-Type",
        "Origin",
        "X-Requested-With",
        "*"
    ],
    expose_headers=["Content-Length", "X-Total-Count"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include API routers
app.include_router(disaster_router)
app.include_router(telegram_router)
app.include_router(openai_router)

# static uploads
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

async def process_item_with_nlp_geocoding(item: Item, text: str) -> Item:
    """Process an item with NLP and geocoding services"""
    if not text:
        return item
    
    # Process text with NLP
    nlp_result = await nlp_service.process_text(text)
    
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
            geocoding_result = await geocoding_service.process_locations(location_texts)
            
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

async def process_item_with_credibility(item: Item, db: Session) -> Item:
    """Process an item with credibility scoring"""
    # If the service method is not async, we can use asyncio.to_thread
    # or make the service method async if it performs I/O operations
    import asyncio
    from functools import partial
    
    # Create a partial function with the arguments
    process_func = partial(credibility_service.process_item_credibility, item, db)
    
    # Run the synchronous function in a thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, process_func)

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
async def ingest_usgs(db: Session = Depends(get_db)):
    try:
        logger.info("Starting USGS data ingestion...")
        data = fetch_usgs_quakes()
        new_count = 0
        
        if not data:
            logger.warning("No data received from USGS API")
            return {"status": "success", "inserted": 0, "total": 0}
        
        for e in data:
            ext_id = e.get("id")
            if not ext_id:
                logger.warning("Skipping USGS entry with missing ID")
                continue
                
            try:
                # Check if this earthquake already exists
                exists = db.query(Item).filter(Item.ext_id == ext_id, Item.source == "USGS").first()
                if exists:
                    continue
                    
                # Extract coordinates - USGS returns [longitude, latitude, depth]
                coords = e.get("coordinates", [])
                if isinstance(coords, list) and len(coords) >= 2:
                    lon, lat = float(coords[0]), float(coords[1])
                    logger.info(f"Extracted coordinates: lon={lon}, lat={lat} for {e.get('place')}")
                else:
                    logger.warning(f"Invalid coordinates for {e.get('place')}: {coords}")
                    lat, lon = None, None
                    
                # Create initial item
                item = Item(
                    ext_id=ext_id,
                    source="USGS",
                    source_handle="USGS",
                    text=e.get("place", "")[:4000],
                    magnitude=float(e.get("mag", 0)) if e.get("mag") is not None else None,
                    place=e.get("place"),
                    lat=lat,
                    lon=lon,
                    raw_json=e
                )
                
                db.add(item)
                await db.commit()
                await db.refresh(item)
                
                try:
                    # Save the basic item first
                    db.add(item)
                    await db.commit()
                    await db.refresh(item)
                    
                    try:
                        # Process with NLP and geocoding
                        item = await process_item_with_nlp_geocoding(item, item.text)
                        
                        # Process with credibility scoring
                        item = await process_item_with_credibility(item, db)
                        
                        # Save the processed item
                        db.add(item)
                        await db.commit()
                    except Exception as proc_error:
                        logger.error(f"Error in post-processing for {ext_id}: {str(proc_error)}")
                        # Continue even if post-processing fails - we still have the basic data
                    
                    new_count += 1
                    
                except Exception as proc_error:
                    logger.error(f"Error processing USGS item {ext_id}: {str(proc_error)}")
                    # Just log the error, don't update status
                    await db.rollback()
                
            except Exception as item_error:
                logger.error(f"Error processing USGS entry {ext_id}: {str(item_error)}")
                continue
        
        logger.info(f"USGS ingestion completed. Inserted {new_count} new items.")
        return {
            "status": "success",
            "inserted": new_count,
            "total": len(data)
        }
        
    except Exception as e:
        error_msg = f"Critical error in USGS ingestion: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "inserted": 0,
            "total": 0
        }

# --- stubs: Reddit & X (use seeds if no API keys yet) ---
def _load_seed(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Seed load failed: {e}")
        return []

@app.get("/ingest/reddit")
async def ingest_reddit(db: Session = Depends(get_db)):
    try:
        seed = _load_seed(os.path.join(os.getcwd(), "seeds", "reddit_seed.json"))
        new = 0
        
        for s in seed:
            ext_id = s.get("id")
            if not ext_id:
                continue
                
            # Check if item already exists
            exists = db.query(Item).filter(Item.ext_id == ext_id, Item.source == "REDDIT").first()
            if exists:
                continue
                
            # Create new item
            item = Item(
                ext_id=ext_id,
                source="REDDIT",
                source_handle=s.get("subreddit"),
                text=((s.get("title") or "") + " - " + (s.get("text") or ""))[:4000],
                place=None,
                lat=s.get("lat"),
                lon=s.get("lon"),
                raw_json=s,
                status="processing"
            )
            db.add(item)
            await db.commit()
            await db.refresh(item)
            
            try:
                # Process with NLP and geocoding
                item = await process_item_with_nlp_geocoding(item, item.text)
                
                # Process with credibility scoring
                item = await process_item_with_credibility(item, db)
                
                # Update status
                item.status = "processed"
                db.add(item)
                await db.commit()
                
                new += 1
                
            except Exception as e:
                logger.error(f"Error processing Reddit item {ext_id}: {str(e)}")
                item.status = f"error: {str(e)[:100]}"
                db.add(item)
                await db.commit()
        
        return {"status": "completed", "inserted": new, "fetched": len(seed)}
        
    except Exception as e:
        logger.error(f"Error in ingest_reddit: {str(e)}")
        return {"status": "error", "error": str(e), "inserted": 0, "fetched": 0}

@app.get("/ingest/seed/x")
async def ingest_seed_x(db: Session = Depends(get_db)):
    try:
        seed = _load_seed(os.path.join(os.getcwd(), "seeds", "x_seed.json"))
        new = 0
        
        for s in seed:
            ext_id = s.get("id")
            if not ext_id:
                continue
                
            # Check if item already exists
            exists = db.query(Item).filter(Item.ext_id == ext_id, Item.source == "X").first()
            if exists:
                continue
                
            # Create new item
            item = Item(
                ext_id=ext_id,
                source="X",
                source_handle=s.get("handle"),
                text=str(s.get("text", ""))[:4000],
                place=None,
                lat=s.get("lat"),
                lon=s.get("lon"),
                raw_json=s,
                status="processing"
            )
            db.add(item)
            await db.commit()
            await db.refresh(item)
            
            try:
                # Process with NLP and geocoding
                item = await process_item_with_nlp_geocoding(item, item.text)
                
                # Process with credibility scoring
                item = await process_item_with_credibility(item, db)
                
                # Update status
                item.status = "processed"
                db.add(item)
                await db.commit()
                
                new += 1
                
            except Exception as e:
                logger.error(f"Error processing X item {ext_id}: {str(e)}")
                item.status = f"error: {str(e)[:100]}"
                db.add(item)
                await db.commit()
        
        return {"status": "completed", "inserted": new, "fetched": len(seed)}
        
    except Exception as e:
        logger.error(f"Error in ingest_seed_x: {str(e)}")
        return {"status": "error", "error": str(e), "inserted": 0, "fetched": 0}

@app.post("/api/ingest")
async def ingest_citizen(
    text: str = Form(...),
    lat: Optional[float] = Form(None),
    lon: Optional[float] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Detect language
    try:
        lang = detect(text)
    except LangDetectException:
        lang = 'en'  # Default to English if detection fails
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
        language=lang,  # Store detected language
        raw_json={"text": text, "lat": lat, "lon": lon, "media_url": media_url}
    )
    
    # Process with NLP and geocoding
    item = await process_item_with_nlp_geocoding(item, text)
    
    # Process with credibility scoring
    item = await process_item_with_credibility(item, db)
    
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"ok": True, "id": item.id, "media_url": media_url}

# --- list items for map ---
@app.get("/api/items")
async def list_items(
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
            "magnitude": float(r.magnitude) if r.magnitude is not None else None,
            "lat": float(r.lat) if r.lat is not None else None,
            "lon": float(r.lon) if r.lon is not None else None,
            "media_url": r.media_url,
            "language": r.language,
            "disaster_type": r.disaster_type,
            "score_credibility": float(r.score_credibility) if r.score_credibility is not None else None,
            "needs_review": r.needs_review,
            "suspected_rumor": r.suspected_rumor,
            "credibility_signals": r.credibility_signals,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else (str(r.created_at) if r.created_at else None)
        }
    
    items_serialized = []
    for r in rows:
        try:
            items_serialized.append(to_dict(r))
        except Exception as ser_err:
            logger.error(f"Error serializing item id={getattr(r, 'id', 'unknown')}: {ser_err}")
            continue
    return {"count": len(items_serialized), "items": items_serialized}

# --- process existing items with NLP and geocoding ---
@app.post("/api/process-nlp-geocoding")
async def process_existing_items(db: Session = Depends(get_db)):
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
                processed_item = await process_item_with_nlp_geocoding(item, item.text)
                
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
async def process_existing_items_credibility(db: Session = Depends(get_db)):
    """Process existing items that don't have credibility scores"""
    try:
        logger.info("Starting credibility processing for existing items...")
        
        # Find items without credibility scores
        items_to_process = db.query(Item).filter(
            Item.score_credibility.is_(None)
        ).limit(100).all()  # Process in batches
        
        if not items_to_process:
            logger.info("No items need credibility processing")
            return {
                "status": "success",
                "message": "No items need credibility processing",
                "processed_count": 0,
                "total_items": db.query(Item).count()
            }
        
        processed_count = 0
        
        for item in items_to_process:
            try:
                # Update status
                item.status = "processing_credibility"
                db.add(item)
                await db.commit()
                await db.refresh(item)
                
                # Process with credibility scoring
                item = await process_item_with_credibility(item, db)
                
                # Update status
                item.status = "processed"
                db.add(item)
                await db.commit()
                
                processed_count += 1
                
                if processed_count % 10 == 0:
                    logger.info(f"Processed {processed_count} items...")
                    
            except Exception as item_error:
                logger.error(f"Error processing item {item.id}: {str(item_error)}")
                try:
                    item.status = f"error_credibility: {str(item_error)[:100]}"
                    db.add(item)
                    await db.commit()
                except Exception as commit_error:
                    logger.error(f"Failed to update item status: {str(commit_error)}")
                continue
        
        logger.info(f"Completed credibility processing. Processed {processed_count} items.")
        
        return {
            "status": "success",
            "processed_count": processed_count,
            "total_items": db.query(Item).count(),
            "message": f"Processed {processed_count} items"
        }
        
    except Exception as e:
        error_msg = f"Error in process_existing_items_credibility: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "processed_count": 0
        }

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
async def load_sample(db: Session = Depends(get_db)):
    # Load USGS data
    usgs_result = await ingest_usgs(db)
    usgs_count = usgs_result.get("inserted", 0) if isinstance(usgs_result, dict) else 0
    logger.info(f"Loaded {usgs_count} items from USGS")
    
    # Load GDACS RSS data
    from ingest import ingest_rss_to_db
    gdacs_count = ingest_rss_to_db(db)
    logger.info(f"Loaded {gdacs_count} items from GDACS")
    
    # Commit any pending changes
    await db.commit()
    
    # Get total items count
    total_items = (await db.execute("SELECT COUNT(*) FROM items")).scalar()
    logger.info(f"Total items in database: {total_items}")
    
    return {
        "status": "ok", 
        "usgs_items": usgs_count,
        "gdacs_items": gdacs_count,
        "total_items": total_items
    }
