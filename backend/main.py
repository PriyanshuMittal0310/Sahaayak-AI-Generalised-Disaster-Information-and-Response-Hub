from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware

from db import Base, engine, get_db
from models import Item
from fetch_usgs import fetch_usgs_quakes

# Ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CrisisConnect API", version="0.3")

# Allow frontend React app (http://localhost:3000) to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, restrict domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    logger.info("🚀 CrisisConnect backend started")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/realtime/earthquakes")
def realtime_quakes(db: Session = Depends(get_db)):
    """
    Fetch and return real-time earthquake data from USGS
    
    Returns:
        JSON response with earthquake events
    """
    events = fetch_usgs_quakes()
    
    if events is None:
        return {"error": "Failed to fetch earthquake data"}, 500
        
    # Store new events in the database
    for event in events:
        if not event.get('id'):
            continue
            
        exists = db.query(Item).filter(Item.id == event["id"]).first()
        if not exists:
            item = Item(
                id=event["id"],
                source="USGS",
                text=event.get("place", ""),
                magnitude=event.get("magnitude"),
                place=event.get("place", ""),
            )
            db.add(item)
            db.commit()
            db.refresh(item)
    
    # Return the events data
    return {"count": len(events), "events": events}