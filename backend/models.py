from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey, Table, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional
from db import Base

# Association table for many-to-many relationship between items and events
item_event_association = Table(
    'item_event_association',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id'), primary_key=True),
    Column('event_id', Integer, ForeignKey('events.id'), primary_key=True)
)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)  # internal PK
    ext_id = Column(String, nullable=True)              # external id (USGS/gdacs/etc)
    source = Column(String, nullable=True)              # 'USGS' | 'GDACS' | 'REDDIT' | 'X' | 'CITIZEN'
    source_handle = Column(String, nullable=True)       # e.g., @user / subreddit / feed url
    text = Column(Text, nullable=True)
    magnitude = Column(Float, nullable=True)
    place = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    media_url = Column(String, nullable=True)           # /uploads/filename.jpg
    raw_json = Column(JSON, nullable=True)
    
    # NLP and Geocoding fields
    language = Column(String, nullable=True)            # detected language code (e.g., 'en', 'es')
    disaster_type = Column(String, nullable=True)       # classified disaster type
    # Note: geom field will be added via migration for PostGIS support

    # Credibility fields
    score_credibility = Column(Float, nullable=True)    # credibility score (0.0-1.0)
    needs_review = Column(String, nullable=True)        # 'true' | 'false' | null
    suspected_rumor = Column(String, nullable=True)     # 'true' | 'false' | null
    credibility_signals = Column(JSON, nullable=True)   # store credibility signals and weights

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to events
    events = relationship('Event', secondary=item_event_association, back_populates='items')
    
    __table_args__ = (UniqueConstraint('ext_id', 'source', name='uq_ext_source'),)


class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)  # Auto-generated title for the event
    description = Column(Text, nullable=True)  # Auto-generated description
    disaster_type = Column(String, nullable=True)  # Type of disaster (earthquake, flood, etc.)
    
    # Location information
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)
    bbox = Column(JSON, nullable=True)  # Bounding box as [min_lon, min_lat, max_lon, max_lat]
    h3_index = Column(String, nullable=True)  # H3 hexagon index for spatial indexing
    
    # Temporal information
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Aggregated metrics
    severity = Column(Float, nullable=True)  # 0-1 scale
    confidence = Column(Float, nullable=True)  # 0-1 scale
    item_count = Column(Integer, default=0)
    source_count = Column(Integer, default=0)  # Number of unique sources
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verification_reason = Column(String, nullable=True)  # Why was this event verified?
    
    # Relationships
    items = relationship('Item', secondary=item_event_association, back_populates='events')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    def update_metrics(self):
        """Update aggregated metrics based on associated items"""
        if not self.items:
            return
            
        # Update item count
        self.item_count = len(self.items)
        
        # Count unique sources
        self.source_count = len({item.source for item in self.items if item.source})
        
        # Update verification status
        self._update_verification()
    
    def _update_verification(self):
        """Update verification status based on criteria"""
        # Check if any official source is present
        official_sources = {'USGS', 'GDACS'}
        has_official = any(item.source in official_sources for item in self.items)
        
        # Check for minimum number of independent sources
        has_enough_sources = self.source_count >= 3
        
        # Update verification status
        if has_official or has_enough_sources:
            self.is_verified = True
            if has_official:
                self.verification_reason = 'official_source'
            else:
                self.verification_reason = f'multiple_sources_{self.source_count}'
        else:
            self.is_verified = False
            self.verification_reason = None
