"""merge multiple heads

Revision ID: 79fcee2882b8
Revises: add_credibility_fields, update_items_table
Create Date: 2025-09-07 09:17:20.291205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79fcee2882b8'
down_revision: Union[str, Sequence[str], None] = ('add_credibility_fields', 'update_items_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
