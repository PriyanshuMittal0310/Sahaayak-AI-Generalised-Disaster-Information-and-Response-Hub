"""
Credibility scoring service for disaster information items.
Implements rules-based credibility scoring as per Day 7 requirements.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math
from sqlalchemy.orm import Session
from models import Item


class CredibilityService:
    """Service for calculating credibility scores and flags for disaster information items."""
    
    def __init__(self):
        # Source baseline weights (official > known > new)
        self.source_weights = {
            'USGS': 0.9,      # Official government source
            'GDACS': 0.8,     # Official international source
            'REDDIT': 0.4,    # Known social platform
            'X': 0.3,         # Known social platform
            'CITIZEN': 0.2,   # New/unknown source
        }
        
        # Media presence boost
        self.media_boost = 0.1
        
        # Corroboration boost (when multiple sources report similar events)
        self.corroboration_boost = 0.15
        
        # Official overlap boost (spatial/time overlap with official sources)
        self.official_overlap_boost = 0.2
        
        # Distance threshold for spatial overlap (in kilometers)
        self.spatial_threshold_km = 50
        
        # Time threshold for temporal overlap (in hours)
        self.temporal_threshold_hours = 24

    def calculate_credibility_score(self, item: Item, db: Session) -> Dict:
        """
        Calculate credibility score and flags for an item.
        
        Returns:
            Dict with score_credibility, needs_review, suspected_rumor, and credibility_signals
        """
        signals = {}
        base_score = 0.0
        
        # 1. Source baseline weights
        source_weight = self.source_weights.get(item.source, 0.1)
        signals['source_weight'] = source_weight
        base_score += source_weight * 0.6  # 60% of base score from source
        
        # 2. Media presence boost
        if item.media_url:
            signals['media_presence'] = True
            base_score += self.media_boost
        else:
            signals['media_presence'] = False
        
        # 3. Corroboration boost (check for similar events from other sources)
        corroboration_score = self._calculate_corroboration_score(item, db)
        signals['corroboration_score'] = corroboration_score
        if corroboration_score > 0:
            base_score += self.corroboration_boost * corroboration_score
        
        # 4. Official overlap boost (spatial/time overlap with official sources)
        official_overlap_score = self._calculate_official_overlap_score(item, db)
        signals['official_overlap_score'] = official_overlap_score
        if official_overlap_score > 0:
            base_score += self.official_overlap_boost * official_overlap_score
        
        # 5. Additional factors
        additional_factors = self._calculate_additional_factors(item)
        signals.update(additional_factors)
        
        # Apply additional factors to base score
        for factor, weight in additional_factors.items():
            if isinstance(weight, (int, float)) and factor != 'source_weight':
                base_score += weight * 0.1  # 10% influence for additional factors
        
        # Normalize score to 0.0-1.0 range
        final_score = min(max(base_score, 0.0), 1.0)
        
        # Determine flags
        needs_review = self._should_need_review(final_score, signals)
        suspected_rumor = self._is_suspected_rumor(final_score, signals, item)
        
        return {
            'score_credibility': final_score,
            'needs_review': 'true' if needs_review else 'false',
            'suspected_rumor': 'true' if suspected_rumor else 'false',
            'credibility_signals': signals
        }

    def _calculate_corroboration_score(self, item: Item, db: Session) -> float:
        """Calculate corroboration score based on similar events from other sources."""
        if not item.lat or not item.lon or not item.created_at:
            return 0.0
        
        # Find similar events within spatial and temporal thresholds
        time_threshold = item.created_at - timedelta(hours=self.temporal_threshold_hours)
        
        similar_items = db.query(Item).filter(
            Item.id != item.id,
            Item.source != item.source,  # Different source
            Item.lat.isnot(None),
            Item.lon.isnot(None),
            Item.created_at >= time_threshold
        ).all()
        
        corroboration_count = 0
        for similar_item in similar_items:
            # Calculate spatial distance
            distance = self._calculate_distance(
                item.lat, item.lon,
                similar_item.lat, similar_item.lon
            )
            
            if distance <= self.spatial_threshold_km:
                # Check for similar disaster type or keywords
                if (item.disaster_type and similar_item.disaster_type and 
                    item.disaster_type == similar_item.disaster_type):
                    corroboration_count += 1
                elif self._has_similar_keywords(item.text, similar_item.text):
                    corroboration_count += 1
        
        # Normalize corroboration score (0.0-1.0)
        return min(corroboration_count / 3.0, 1.0)  # Max boost at 3+ corroborations

    def _calculate_official_overlap_score(self, item: Item, db: Session) -> float:
        """Calculate official overlap score based on spatial/time overlap with official sources."""
        if not item.lat or not item.lon or not item.created_at:
            return 0.0
        
        # Find official sources (USGS, GDACS) within spatial and temporal thresholds
        time_threshold = item.created_at - timedelta(hours=self.temporal_threshold_hours)
        
        official_items = db.query(Item).filter(
            Item.source.in_(['USGS', 'GDACS']),
            Item.lat.isnot(None),
            Item.lon.isnot(None),
            Item.created_at >= time_threshold
        ).all()
        
        overlap_count = 0
        for official_item in official_items:
            # Calculate spatial distance
            distance = self._calculate_distance(
                item.lat, item.lon,
                official_item.lat, official_item.lon
            )
            
            if distance <= self.spatial_threshold_km:
                overlap_count += 1
        
        # Normalize overlap score (0.0-1.0)
        return min(overlap_count / 2.0, 1.0)  # Max boost at 2+ official overlaps

    def _calculate_additional_factors(self, item: Item) -> Dict:
        """Calculate additional credibility factors."""
        factors = {}
        
        # Text quality factors
        if item.text:
            text_length = len(item.text)
            factors['text_length'] = text_length
            
            # Longer, more detailed text gets slight boost
            if text_length > 100:
                factors['detailed_text'] = 0.05
            elif text_length < 20:
                factors['brief_text'] = -0.1
        
        # Place information quality
        if item.place and len(item.place) > 5:
            factors['has_place_info'] = 0.05
        
        # Coordinate precision
        if item.lat and item.lon:
            factors['has_coordinates'] = 0.1
            # Check for suspicious coordinates (0,0 or very round numbers)
            if (item.lat == 0.0 and item.lon == 0.0) or \
               (abs(item.lat) < 0.001 and abs(item.lon) < 0.001):
                factors['suspicious_coordinates'] = -0.2
        
        # Magnitude information (for earthquakes)
        if item.magnitude is not None:
            factors['has_magnitude'] = 0.05
            # Very high magnitudes might be suspicious
            if item.magnitude > 9.0:
                factors['extreme_magnitude'] = -0.1
        
        return factors

    def _should_need_review(self, score: float, signals: Dict) -> bool:
        """Determine if item needs manual review."""
        # Low credibility score
        if score < 0.3:
            return True
        
        # Suspicious coordinates
        if signals.get('suspicious_coordinates'):
            return True
        
        # No source information
        if signals.get('source_weight', 0) < 0.2:
            return True
        
        # Very brief text
        if signals.get('brief_text'):
            return True
        
        return False

    def _is_suspected_rumor(self, score: float, signals: Dict, item: Item) -> bool:
        """Determine if item is suspected to be a rumor."""
        # Very low credibility score
        if score < 0.2:
            return True
        
        # No corroboration and low source weight
        if (signals.get('corroboration_score', 0) == 0 and 
            signals.get('source_weight', 0) < 0.3):
            return True
        
        # Suspicious coordinates
        if signals.get('suspicious_coordinates'):
            return True
        
        # Check for rumor-like keywords in text
        if item.text and self._contains_rumor_keywords(item.text):
            return True
        
        return False

    def _contains_rumor_keywords(self, text: str) -> bool:
        """Check if text contains rumor-like keywords."""
        rumor_keywords = [
            'rumor', 'heard', 'someone said', 'friend told me',
            'unconfirmed', 'allegedly', 'supposedly', 'apparently',
            'not sure', 'might be', 'could be', 'possibly'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in rumor_keywords)

    def _has_similar_keywords(self, text1: str, text2: str) -> bool:
        """Check if two texts have similar disaster-related keywords."""
        if not text1 or not text2:
            return False
        
        disaster_keywords = [
            'earthquake', 'flood', 'fire', 'storm', 'hurricane', 'tornado',
            'disaster', 'emergency', 'evacuation', 'damage', 'injury',
            'casualty', 'rescue', 'help', 'shelter'
        ]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        keywords1 = [kw for kw in disaster_keywords if kw in text1_lower]
        keywords2 = [kw for kw in disaster_keywords if kw in text2_lower]
        
        # Check for overlap in disaster keywords
        return len(set(keywords1) & set(keywords2)) > 0

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def process_item_credibility(self, item: Item, db: Session) -> Item:
        """Process an item and update its credibility fields."""
        credibility_data = self.calculate_credibility_score(item, db)
        
        item.score_credibility = credibility_data['score_credibility']
        item.needs_review = credibility_data['needs_review']
        item.suspected_rumor = credibility_data['suspected_rumor']
        item.credibility_signals = credibility_data['credibility_signals']
        
        return item


# Global instance
credibility_service = CredibilityService()
