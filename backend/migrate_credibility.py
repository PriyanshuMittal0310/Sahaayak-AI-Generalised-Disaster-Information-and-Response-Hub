#!/usr/bin/env python3
"""
Simple migration script to add credibility columns
"""

from db import engine
from sqlalchemy import text

def migrate_credibility_columns():
    """Add credibility columns to items table"""
    try:
        with engine.connect() as conn:
            # Add credibility columns
            conn.execute(text('ALTER TABLE items ADD COLUMN IF NOT EXISTS score_credibility FLOAT'))
            conn.execute(text('ALTER TABLE items ADD COLUMN IF NOT EXISTS needs_review VARCHAR'))
            conn.execute(text('ALTER TABLE items ADD COLUMN IF NOT EXISTS suspected_rumor VARCHAR'))
            conn.execute(text('ALTER TABLE items ADD COLUMN IF NOT EXISTS credibility_signals JSON'))
            conn.commit()
            print("✅ Credibility columns added successfully")
    except Exception as e:
        print(f"❌ Error adding columns: {e}")

if __name__ == "__main__":
    migrate_credibility_columns()
