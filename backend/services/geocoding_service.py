import os
from typing import Optional, Dict, List, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from shapely.geometry import Point
from loguru import logger
import time

class GeocodingService:
    def __init__(self):
        self.geocoder = Nominatim(user_agent="sahaayak-disaster-hub/1.0")
        self.rate_limit_delay = 1.0  # seconds between requests
        
    def geocode_location(self, location_text: str, country_code: Optional[str] = None) -> Optional[Dict[str, any]]:
        """
        Geocode a location string to get coordinates and formatted address
        
        Args:
            location_text: The location string to geocode
            country_code: Optional country code to bias results (e.g., 'US', 'IN')
            
        Returns:
            Dict with lat, lon, formatted_address, confidence, and raw data
        """
        if not location_text or not location_text.strip():
            return None
            
        try:
            # Add country bias if provided
            query = location_text.strip()
            if country_code:
                query = f"{query}, {country_code}"
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            # Geocode the location
            location = self.geocoder.geocode(query, exactly_one=True, timeout=10)
            
            if location:
                return {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'formatted_address': location.address,
                    'confidence': 0.8,  # Nominatim doesn't provide confidence scores
                    'raw_data': {
                        'raw': location.raw,
                        'point': location.point
                    }
                }
            else:
                logger.warning(f"No geocoding results for: {location_text}")
                return None
                
        except GeocoderTimedOut:
            logger.error(f"Geocoding timeout for: {location_text}")
            return None
        except GeocoderServiceError as e:
            logger.error(f"Geocoding service error for {location_text}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected geocoding error for {location_text}: {e}")
            return None
    
    def geocode_multiple_locations(self, locations: List[str], country_code: Optional[str] = None) -> List[Dict[str, any]]:
        """
        Geocode multiple locations and return results
        
        Args:
            locations: List of location strings to geocode
            country_code: Optional country code to bias results
            
        Returns:
            List of geocoding results (None for failed geocoding)
        """
        results = []
        
        for location in locations:
            result = self.geocode_location(location, country_code)
            results.append(result)
            
        return results
    
    def get_best_location(self, locations: List[Dict[str, any]]) -> Optional[Dict[str, any]]:
        """
        Select the best location from multiple geocoding results
        
        Args:
            locations: List of geocoding results
            
        Returns:
            Best geocoding result based on confidence and other factors
        """
        if not locations:
            return None
            
        # Filter out None results
        valid_locations = [loc for loc in locations if loc is not None]
        
        if not valid_locations:
            return None
            
        # If only one valid result, return it
        if len(valid_locations) == 1:
            return valid_locations[0]
            
        # Sort by confidence (if available) and other factors
        def location_score(loc):
            score = loc.get('confidence', 0.5)
            
            # Prefer locations with more complete addresses
            address = loc.get('formatted_address', '')
            if len(address.split(',')) > 2:  # More specific address
                score += 0.1
                
            return score
            
        # Return the location with highest score
        best_location = max(valid_locations, key=location_score)
        return best_location
    
    def create_geometry(self, lat: float, lon: float) -> Optional[str]:
        """
        Create a PostGIS geometry WKT string from lat/lon coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            WKT geometry string for PostGIS
        """
        try:
            if lat is None or lon is None:
                return None
                
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                logger.warning(f"Invalid coordinates: lat={lat}, lon={lon}")
                return None
                
            # Return WKT format for PostGIS
            return f"POINT({lon} {lat})"
            
        except Exception as e:
            logger.error(f"Error creating geometry: {e}")
            return None
    
    def process_locations(self, location_texts: List[str], country_code: Optional[str] = None) -> Optional[Dict[str, any]]:
        """
        Process multiple location texts and return the best geocoded result
        
        Args:
            location_texts: List of location strings to process
            country_code: Optional country code to bias results
            
        Returns:
            Best geocoding result with geometry
        """
        if not location_texts:
            return None
            
        # Geocode all locations
        geocoded_results = self.geocode_multiple_locations(location_texts, country_code)
        
        # Get the best result
        best_result = self.get_best_location(geocoded_results)
        
        if best_result:
            # Add geometry
            lat = best_result.get('lat')
            lon = best_result.get('lon')
            if lat and lon:
                best_result['geometry'] = self.create_geometry(lat, lon)
            
        return best_result

# Global instance
geocoding_service = GeocodingService()
