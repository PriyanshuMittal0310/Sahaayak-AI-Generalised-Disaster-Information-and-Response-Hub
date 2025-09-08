from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel
from datetime import datetime

from services.nlp_service import nlp_service

router = APIRouter(prefix="/api/disasters", tags=["disaster-detection"])
logger = logging.getLogger(__name__)

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
        raise HTTPException(status_code=500, detail=str(e))
