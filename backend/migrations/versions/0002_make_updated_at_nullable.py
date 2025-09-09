"""make updated_at nullable in events

Revision ID: 0002_make_updated_at_nullable
Revises: 0001_initial
Create Date: 2025-09-09 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_make_updated_at_nullable'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade():
    # Make updated_at nullable
    op.alter_column('events', 'updated_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True,
               existing_server_default=sa.text('now()'))

def downgrade():
    # Revert to not nullable
    op.alter_column('events', 'updated_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
