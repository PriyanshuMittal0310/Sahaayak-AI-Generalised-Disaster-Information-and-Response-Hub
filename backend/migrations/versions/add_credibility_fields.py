"""Add credibility fields to items table

Revision ID: add_credibility_fields
Revises: add_nlp_geocoding_fields
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_credibility_fields'
down_revision = 'add_nlp_geocoding_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add credibility fields to items table
    op.add_column('items', sa.Column('score_credibility', sa.Float(), nullable=True))
    op.add_column('items', sa.Column('needs_review', sa.String(), nullable=True))
    op.add_column('items', sa.Column('suspected_rumor', sa.String(), nullable=True))
    op.add_column('items', sa.Column('credibility_signals', sa.JSON(), nullable=True))


def downgrade():
    # Remove credibility fields from items table
    op.drop_column('items', 'credibility_signals')
    op.drop_column('items', 'suspected_rumor')
    op.drop_column('items', 'needs_review')
    op.drop_column('items', 'score_credibility')
