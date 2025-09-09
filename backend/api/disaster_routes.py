from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict, Any, Optional, Union
import logging
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from services.nlp_service import nlp_service
from services.event_service import EventService
from db import get_db
from models import Event, Item

router = APIRouter(prefix="/api/disasters", tags=["disaster-detection"])
logger = logging.getLogger(__name__)

# Response models
class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    disaster_type: Optional[str] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    bbox: Optional[List[float]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    severity: Optional[float] = None
    confidence: Optional[float] = None
    item_count: int = 0
    source_count: int = 0
    is_verified: bool = False
    verification_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    page: int
    page_size: int

class TextInput(BaseModel):
    text: str
    detect_language: bool = True
    use_openai: bool = False

class DisasterDetectionResult(BaseModel):
    text: str
    language: Optional[str] = None
    disaster_type: Optional[str] = None
    disaster_severity: Optional[str] = None
    disaster_confidence: Optional[float] = None
    sentiment: Optional[Dict[str, float]] = None
    locations: List[Dict[str, Any]] = []
    entities: List[Dict[str, Any]] = []
    timestamp: str = datetime.utcnow().isoformat()

@router.post("/detect", response_model=DisasterDetectionResult)
async def detect_disaster(input_data: TextInput):
    """
    Analyze text for disaster-related information including type, severity, and locations.
    
    - **text**: The text to analyze
    - **detect_language**: Whether to automatically detect the language (default: True)
    - **use_openai**: Whether to use OpenAI for enhanced detection (requires API key)
    """
    try:
        # Process the text through our NLP pipeline
        result = await nlp_service.process_text(input_data.text)
        
        # Ensure all required fields are present in the response
        response_data = {
            "text": input_data.text,  # Include the original text
            "language": result.get("language"),
            "disaster_type": result.get("disaster_type"),
            "disaster_severity": result.get("disaster_severity"),
            "disaster_confidence": float(result.get("disaster_confidence", 0.0)),
            "sentiment": {k: float(v) for k, v in result.get("sentiment", {}).items()},
            "locations": result.get("locations", []),
            "entities": result.get("entities", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in disaster detection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-detect", response_model=List[DisasterDetectionResult])
async def batch_detect_disasters(inputs: List[TextInput]):
    """
    Process multiple texts for disaster detection in a single request.
    """
    try:
        results = []
        for input_data in inputs:
            try:
                # Process the text through our NLP pipeline
                result = await nlp_service.process_text(input_data.text)
                
                # Ensure all required fields are present in the response
                response_data = {
                    "text": input_data.text,
                    "language": result.get("language"),
                    "disaster_type": result.get("disaster_type"),
                    "disaster_severity": result.get("disaster_severity"),
                    "disaster_confidence": float(result.get("disaster_confidence", 0.0)),
                    "sentiment": {k: float(v) for k, v in result.get("sentiment", {}).items()},
                    "locations": result.get("locations", []),
                    "entities": result.get("entities", []),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                results.append(response_data)
                
            except Exception as e:
                logger.error(f"Error processing text: {input_data.text[:100]}... Error: {str(e)}")
                results.append({
                    "text": input_data.text,
                    "error": str(e)
                })
                
        return results
        
    except Exception as e:
        logger.error(f"Error in batch disaster detection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=EventListResponse)
async def list_events(
    db: Session = Depends(get_db),
    disaster_type: Optional[str] = None,
    verified: Optional[bool] = None,
    bbox: Optional[str] = None,  # format: min_lon,min_lat,max_lon,max_lat
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List disaster events with filtering and pagination.
    """
    try:
        query = db.query(Event)
        
        # Apply filters
        if disaster_type:
            query = query.filter(Event.disaster_type == disaster_type)
            
        if verified is not None:
            query = query.filter(Event.is_verified == verified)
            
        if bbox:
            try:
                min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(','))
                query = query.filter(
                    Event.centroid_lon.between(min_lon, max_lon),
                    Event.centroid_lat.between(min_lat, max_lat)
                )
            except (ValueError, AttributeError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid bbox format. Use: min_lon,min_lat,max_lon,max_lat"
                )
                
        if start_time:
            query = query.filter(Event.start_time >= start_time)
            
        if end_time:
            query = query.filter(Event.end_time <= end_time)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        events = query.order_by(Event.start_time.desc())\
                     .offset((page - 1) * page_size)\
                     .limit(page_size)\
                     .all()
        
        return {
            "events": events,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        logger.error(f"Error listing events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """
    Get details of a specific event.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/events/{event_id}/items")
async def get_event_items(
    event_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get items associated with an event.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    items = db.query(Item)\
             .join(item_event_association)\
             .filter(item_event_association.c.event_id == event_id)\
             .order_by(Item.created_at.desc())\
             .offset((page - 1) * page_size)\
             .limit(page_size)\
             .all()
             
    total = len(event.items)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.post("/events/{event_id}/verify", response_model=EventResponse)
async def verify_event(
    event_id: int,
    verify: bool = True,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Manually verify or unverify an event.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    event.is_verified = verify
    event.verification_reason = reason or "manually_verified" if verify else None
    
    db.commit()
    db.refresh(event)
    
    return event

@router.post("/events/recluster")
async def trigger_recluster(db: Session = Depends(get_db)):
    """
    Trigger reclustering of unclustered items.
    """
    try:
        event_service = EventService(db)
        new_events = event_service.recluster_events()
        return {
            "status": "success",
            "new_events_created": len(new_events)
        }
    except Exception as e:
        logger.error(f"Error during reclustering: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
