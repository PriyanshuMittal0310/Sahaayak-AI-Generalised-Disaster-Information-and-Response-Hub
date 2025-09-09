import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import h3
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from models import Item, Event, item_event_association

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self, db: Session):
        self.db = db
        
        # Configuration parameters (can be moved to config)
        self.h3_resolution = 5  # H3 resolution for spatial indexing (0-15, where 15 is most precise)
        self.time_window_hours = 24  # Time window for temporal clustering
        self.min_cluster_size = 2  # Minimum items to form a cluster
        self.eps_km = 10.0  # Maximum distance in km for DBSCAN
        self.min_samples = 2  # Minimum samples per cluster for DBSCAN
    
    def process_new_item(self, item_id: int) -> Optional[Event]:
        """Process a new item and assign it to an existing or new event."""
        item = self.db.query(Item).filter(Item.id == item_id).first()
        if not item or not item.lat or not item.lon:
            return None
            
        # Find existing events that could match this item
        matching_events = self._find_matching_events(item)
        
        if matching_events:
            # Add to the best matching event
            best_event = matching_events[0]
            self._add_item_to_event(item, best_event)
            return best_event
        else:
            # Create a new event
            return self._create_new_event([item])
    
    def recluster_events(self) -> List[Event]:
        """Recluster all unclustered items and update existing clusters."""
        # Get all items not yet in any event
        unclustered_items = self.db.query(Item).outerjoin(
            item_event_association
        ).filter(
            item_event_association.c.item_id.is_(None)
        ).all()
        
        if not unclustered_items:
            return []
            
        # Cluster unclustered items
        clusters = self._cluster_items(unclustered_items)
        
        # Create new events for each cluster
        new_events = []
        for cluster_items in clusters:
            event = self._create_new_event(cluster_items)
            if event:
                new_events.append(event)
                
        return new_events
    
    def _find_matching_events(self, item: Item) -> List[Event]:
        """Find existing events that could match the given item."""
        # Calculate time window bounds
        time_window_start = item.created_at - timedelta(hours=self.time_window_hours)
        
        # Get events in the same H3 cell and time window
        h3_index = h3.geo_to_h3(item.lat, item.lon, self.h3_resolution)
        
        matching_events = self.db.query(Event).filter(
            Event.h3_index == h3_index,
            Event.start_time >= time_window_start,
            Event.disaster_type == item.disaster_type  # Only match same disaster types
        ).all()
        
        # Sort by distance to event centroid (closest first)
        matching_events.sort(
            key=lambda e: great_circle(
                (item.lat, item.lon), 
                (e.centroid_lat, e.centroid_lon)
            ).km
        )
        
        return matching_events
    
    def _add_item_to_event(self, item: Item, event: Event) -> None:
        """Add an item to an existing event."""
        if item not in event.items:
            event.items.append(item)
            
            # Update event metadata
            if not event.start_time or item.created_at < event.start_time:
                event.start_time = item.created_at
            if not event.end_time or item.created_at > event.end_time:
                event.end_time = item.created_at
                
            # Update spatial bounds
            self._update_event_geography(event)
            
            # Update metrics and verification status
            event.update_metrics()
            
            self.db.commit()
    
    def _create_new_event(self, items: List[Item]) -> Optional[Event]:
        """Create a new event from a list of items."""
        if not items:
            return None
            
        # Create the event
        event = Event(
            disaster_type=items[0].disaster_type,
            start_time=min(item.created_at for item in items),
            end_time=max(item.created_at for item in items)
        )
        
        # Add items to event
        event.items = items
        
        # Set initial spatial data
        self._update_event_geography(event)
        
        # Set initial metrics and verification
        event.update_metrics()
        
        # Generate a title and description
        self._generate_event_summary(event)
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event
    
    def _update_event_geography(self, event: Event) -> None:
        """Update the geographic properties of an event based on its items."""
        if not event.items:
            return
            
        # Calculate centroid
        lats = [item.lat for item in event.items if item.lat is not None]
        lons = [item.lon for item in event.items if item.lon is not None]
        
        if lats and lons:
            event.centroid_lat = sum(lats) / len(lats)
            event.centroid_lon = sum(lons) / len(lons)
            
            # Update H3 index
            event.h3_index = h3.geo_to_h3(
                event.centroid_lat, 
                event.centroid_lon, 
                self.h3_resolution
            )
            
            # Update bounding box
            event.bbox = [
                min(lons),  # min_lon
                min(lats),  # min_lat
                max(lons),  # max_lon
                max(lats)   # max_lat
            ]
    
    def _generate_event_summary(self, event: Event) -> None:
        """Generate a title and description for the event based on its items."""
        if not event.items:
            return
            
        # Get the most common disaster type
        disaster_types = [item.disaster_type for item in event.items if item.disaster_type]
        most_common_type = max(set(disaster_types), key=disaster_types.count) if disaster_types else "disaster"
        
        # Get location from the most credible source
        location = next((item.place for item in event.items if item.place), "an unknown location")
        
        # Generate title and description
        event.title = f"{most_common_type.capitalize()} in {location}"
        event.description = (
            f"A {most_common_type} event was reported in {location} with {len(event.items)} "
            f"related reports from {event.source_count} different sources."
        )
    
    def _cluster_items(self, items: List[Item]) -> List[List[Item]]:
        """Cluster items using DBSCAN with spatiotemporal constraints."""
        if not items:
            return []
            
        # Prepare data for clustering
        coords = np.array([
            [item.lat, item.lon, self._datetime_to_timestamp(item.created_at)]
            for item in items
            if item.lat is not None and item.lon is not None
        ])
        
        if len(coords) < self.min_cluster_size:
            return []
        
        # Normalize coordinates (latitude/longitude in degrees, time in hours)
        # This helps DBSCAN work with different units
        coords_norm = coords.copy()
        coords_norm[:, 0] = coords_norm[:, 0] * 111.32  # approx km per degree latitude
        coords_norm[:, 1] = coords_norm[:, 1] * 111.32 * np.cos(np.radians(coords[:, 0]))  # approx km per degree longitude
        coords_norm[:, 2] = coords_norm[:, 2] / 3600  # convert seconds to hours
        
        # Apply DBSCAN clustering
        db = DBSCAN(
            eps=self.eps_km,
            min_samples=self.min_samples,
            metric='euclidean',
            n_jobs=-1
        ).fit(coords_norm)
        
        # Group items by cluster
        clusters: Dict[int, List[Item]] = {}
        for idx, label in enumerate(db.labels_):
            if label == -1:  # Noise points
                continue
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(items[idx])
        
        return list(clusters.values())
    
    @staticmethod
    def _datetime_to_timestamp(dt: datetime) -> float:
        """Convert datetime to timestamp (seconds since epoch)."""
        return dt.timestamp()
