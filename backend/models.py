from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from db import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True, index=True)
    source = Column(String, nullable=True)
    text = Column(String, nullable=True)
    magnitude = Column(Float, nullable=True)
    place = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
