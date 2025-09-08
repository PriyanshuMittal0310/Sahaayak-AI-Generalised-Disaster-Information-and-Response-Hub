import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the database configuration
from db import engine, Base

def test_db_connection():
    try:
        # Test the connection
        with engine.connect() as connection:
            print("✅ Successfully connected to the database!")
            
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get table information
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("\n📊 Database Tables:")
        for table in tables:
            print(f"- {table}")
            
        # Check if the items table exists and has data
        if 'items' in tables:
            from sqlalchemy import text
            result = session.execute(text("SELECT COUNT(*) FROM items"))
            count = result.scalar()
            print(f"\n📦 Items table has {count} records")
            
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to the database: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Testing database connection...")
    test_db_connection()
