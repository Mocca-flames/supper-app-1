"""Update Order model types

Revision ID: 2af61ddd0063
Revises: 385dc291a7c2
Create Date: 2025-08-03 16:28:28.120621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2af61ddd0063'
down_revision: Union[str, None] = '385dc291a7c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
