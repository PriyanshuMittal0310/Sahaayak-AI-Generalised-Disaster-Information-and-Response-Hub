"""update_items_table

Revision ID: update_items_table
Revises: f428361a56b6
Create Date: 2024-09-06 21:45:14.000591

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'update_items_table'
down_revision = 'f428361a56b6'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns if they don't exist
    op.add_column('items', sa.Column('text', sa.Text(), nullable=True))
    op.add_column('items', sa.Column('magnitude', sa.Float(), nullable=True))
    op.add_column('items', sa.Column('place', sa.String(), nullable=True))
    op.add_column('items', sa.Column('lat', sa.Float(), nullable=True))
    op.add_column('items', sa.Column('lon', sa.Float(), nullable=True))
    op.add_column('items', sa.Column('media_url', sa.String(), nullable=True))
    op.add_column('items', sa.Column('raw_json', sa.JSON(), nullable=True))
    op.add_column('items', sa.Column('language', sa.String(), nullable=True))
    op.add_column('items', sa.Column('disaster_type', sa.String(), nullable=True))
    op.add_column('items', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    
    # Add PostGIS extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Add geometry column
    op.execute('ALTER TABLE items ADD COLUMN IF NOT EXISTS geom GEOMETRY(Point, 4326)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_items_geom ON items USING GIST(geom)')

def downgrade():
    # Drop columns
    op.drop_column('items', 'text')
    op.drop_column('items', 'magnitude')
    op.drop_column('items', 'place')
    op.drop_column('items', 'lat')
    op.drop_column('items', 'lon')
    op.drop_column('items', 'media_url')
    op.drop_column('items', 'raw_json')
    op.drop_column('items', 'language')
    op.drop_column('items', 'disaster_type')
    op.drop_column('items', 'created_at')
    op.drop_column('items', 'geom')
    op.execute('DROP INDEX IF EXISTS idx_items_geom')
