"""Merge heads

Revision ID: 3743f59852c0
Revises: add_gateway_field_to_payments, c038d2821cd1
Create Date: 2025-10-09 13:03:19.706414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3743f59852c0'
down_revision: Union[str, None] = ('add_gateway_field_to_payments', 'c038d2821cd1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
