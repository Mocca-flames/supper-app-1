"""Add placeholder revision

Revision ID: 4ff61f9b0695
Revises: da0c9b883986
Create Date: 2025-08-02 14:06:59.079026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ff61f9b0695'
down_revision: Union[str, None] = 'da0c9b883986'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
