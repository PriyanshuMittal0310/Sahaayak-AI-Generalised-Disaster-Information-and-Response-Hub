"""add_nlp_geocoding_fields

Revision ID: add_nlp_geocoding_fields
Revises: f428361a56b6
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_nlp_geocoding_fields'
down_revision = 'f428361a56b6'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to items table
    op.add_column('items', sa.Column('language', sa.String(), nullable=True))
    op.add_column('items', sa.Column('disaster_type', sa.String(), nullable=True))
    
    # Add PostGIS geometry column using raw SQL
    op.execute("ALTER TABLE items ADD COLUMN geom GEOMETRY(POINT, 4326)")
    
    # Create spatial index on geometry column
    op.execute("CREATE INDEX idx_items_geom ON items USING GIST (geom)")


def downgrade():
    # Drop spatial index
    op.drop_index('idx_items_geom', table_name='items')
    
    # Drop columns
    op.drop_column('items', 'geom')
    op.drop_column('items', 'disaster_type')
    op.drop_column('items', 'language')
