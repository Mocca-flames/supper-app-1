"""Change order id to UUID type

Revision ID: 385dc291a7c2
Revises: c5a3d6a68f86
Create Date: 2025-08-03 17:51:19.602615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '385dc291a7c2'
down_revision: Union[str, None] = 'c5a3d6a68f86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
