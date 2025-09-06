from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, UniqueConstraint
from sqlalchemy.sql import func
from db import Base

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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('ext_id', 'source', name='uq_ext_source'),)
