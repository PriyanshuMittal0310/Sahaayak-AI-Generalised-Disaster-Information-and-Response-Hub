import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from models import Base, Item, Event
from services.event_service import EventService

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"

def setup_test_db():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db_session():
    engine = setup_test_db()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

def test_create_event_with_items(db_session):
    # Create test items
    now = datetime.utcnow()
    items = [
        Item(
            source="TWITTER",
            text="Earthquake in San Francisco!",
            lat=37.7749,
            lon=-122.4194,
            disaster_type="earthquake",
            created_at=now - timedelta(minutes=30)
        ),
        Item(
            source="REDDIT",
            text="Felt an earthquake in SF just now",
            lat=37.7750,
            lon=-122.4195,
            disaster_type="earthquake",
            created_at=now - timedelta(minutes=25)
        ),
        Item(
            source="USGS",
            text="M 4.5 - 3km NE of San Francisco, CA",
            lat=37.7760,
            lon=-122.4180,
            disaster_type="earthquake",
            created_at=now - timedelta(minutes=20)
        )
    ]
    
    db_session.add_all(items)
    db_session.commit()
    
    # Create event service and process items
    event_service = EventService(db_session)
    
    # Process first item - should create a new event
    event1 = event_service.process_new_item(items[0].id)
    assert event1 is not None
    assert len(event1.items) == 1
    assert event1.disaster_type == "earthquake"
    assert not event1.is_verified
    
    # Process second item - should add to existing event
    event2 = event_service.process_new_item(items[1].id)
    assert event2.id == event1.id
    assert len(event2.items) == 2
    assert not event2.is_verified
    
    # Process third item (from USGS) - should verify the event
    event3 = event_service.process_new_item(items[2].id)
    assert event3.id == event1.id
    assert len(event3.items) == 3
    assert event3.is_verified
    assert event3.verification_reason == "official_source"
    assert event3.source_count == 3

def test_recluster_events(db_session):
    # Create test items that should form a cluster
    now = datetime.utcnow()
    items = [
        Item(
            source=f"SOURCE_{i}",
            text=f"Test earthquake {i}",
            lat=37.7749 + (i * 0.01),  # Slightly different locations
            lon=-122.4194 + (i * 0.01),
            disaster_type="earthquake",
            created_at=now - timedelta(minutes=30 - i)
        ) for i in range(5)
    ]
    
    db_session.add_all(items)
    db_session.commit()
    
    # Create event service and trigger reclustering
    event_service = EventService(db_session)
    events = event_service.recluster_events()
    
    # Should create one event with all items
    assert len(events) == 1
    event = events[0]
    assert len(event.items) == 5
    assert event.source_count == 5
    assert event.is_verified  # Should be verified due to >= 3 sources
    assert "multiple_sources_5" in event.verification_reason

def test_event_geography(db_session):
    # Create a test event with items
    items = [
        Item(
            source="TEST",
            text="Test location 1",
            lat=10.0,
            lon=20.0,
            disaster_type="test",
            created_at=datetime.utcnow()
        ),
        Item(
            source="TEST",
            text="Test location 2",
            lat=10.1,
            lon=20.1,
            disaster_type="test",
            created_at=datetime.utcnow()
        )
    ]
    
    db_session.add_all(items)
    db_session.commit()
    
    # Create event and add items
    event = Event(disaster_type="test")
    event.items = items
    db_session.add(event)
    db_session.commit()
    
    # Update geography
    event_service = EventService(db_session)
    event_service._update_event_geography(event)
    
    # Check calculated values
    assert event.centroid_lat == pytest.approx(10.05)
    assert event.centroid_lon == pytest.approx(20.05)
    assert event.bbox == [20.0, 10.0, 20.1, 10.1]
    assert event.h3_index is not None
