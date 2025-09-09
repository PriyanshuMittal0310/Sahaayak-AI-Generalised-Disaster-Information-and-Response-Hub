"""Initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2023-09-09 14:45:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create items table
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('ext_id', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('source_handle', sa.String(), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('magnitude', sa.Float(), nullable=True),
        sa.Column('place', sa.String(), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('media_url', sa.String(), nullable=True),
        sa.Column('raw_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('disaster_type', sa.String(), nullable=True),
        sa.Column('score_credibility', sa.Float(), nullable=True),
        sa.Column('needs_review', sa.String(), nullable=True),
        sa.Column('suspected_rumor', sa.String(), nullable=True),
        sa.Column('credibility_signals', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('ext_id', 'source', name='uq_ext_source')
    )
    
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('disaster_type', sa.String(), nullable=True),
        sa.Column('centroid_lat', sa.Float(), nullable=True),
        sa.Column('centroid_lon', sa.Float(), nullable=True),
        sa.Column('bbox', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('h3_index', sa.String(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('severity', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('item_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('source_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('verification_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False)
    )
    
    # Create item_event_association table
    op.create_table(
        'item_event_association',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.id']),
        sa.PrimaryKeyConstraint('item_id', 'event_id')
    )
    
    # Create regular indexes
    op.create_index('ix_events_disaster_type', 'events', ['disaster_type'], unique=False)
    op.create_index('ix_events_h3_index', 'events', ['h3_index'], unique=False)
    op.create_index('ix_events_start_time', 'events', ['start_time'], unique=False)
    op.create_index('ix_events_is_verified', 'events', ['is_verified'], unique=False)
    
    # Skip PostGIS for now - we'll add it later if needed
    print("Skipping PostGIS spatial index creation. Will be added in a separate migration.")
    # Create a placeholder for the spatial index that will be added later
    op.execute(sa.text("SELECT 1"))  # Just to ensure we have a valid operation

def downgrade():
    # Drop indexes first
    try:
        op.execute(sa.text("DROP INDEX IF EXISTS idx_events_centroid"))
    except:
        pass  # Ignore if index doesn't exist
    
    # Drop regular indexes
    op.drop_index('ix_events_is_verified', table_name='events')
    op.drop_index('ix_events_start_time', table_name='events')
    op.drop_index('ix_events_h3_index', table_name='events')
    op.drop_index('ix_events_disaster_type', table_name='events')
    
    # Drop tables
    op.drop_table('item_event_association')
    op.drop_table('events')
    op.drop_table('items')
