"""Update order status column type to String

Revision ID: c5a3d6a68f86
Revises: 4ab1f928c359
Create Date: 2025-08-03 15:50:02.480470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5a3d6a68f86'
down_revision: Union[str, None] = '4ab1f928c359'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
